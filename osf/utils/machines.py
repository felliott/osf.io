from django.utils import timezone
from django.db import IntegrityError
from transitions import Machine, MachineError

from api.providers.workflows import Workflows
from framework.auth import Auth

from osf.exceptions import InvalidTransitionError
from osf.models.preprintlog import PreprintLog
from osf.models.action import ReviewAction, NodeRequestAction, PreprintRequestAction
from osf.utils import permissions
from osf.utils.workflows import (
    DefaultStates,
    DefaultTriggers,
    ReviewStates,
    ApprovalStates,
    DEFAULT_TRANSITIONS,
    REVIEWABLE_TRANSITIONS,
    APPROVAL_TRANSITIONS,
    CollectionSubmissionStates,
    COLLECTION_SUBMISSION_TRANSITIONS,
    NodeRequestTypes
)
from website.mails import mails
from website.reviews import signals as reviews_signals
from website.settings import DOMAIN, OSF_SUPPORT_EMAIL, OSF_CONTACT_EMAIL

from osf.utils import notifications as notify

from api.base.exceptions import Conflict

class BaseMachine(Machine):

    action = None
    from_state = None
    States = DefaultStates
    Transitions = DEFAULT_TRANSITIONS

    def __init__(self, machineable, state_attr='machine_state'):
        """
        Welcome to the machine, this is our attempt at a state machine. It was written for nodes, prerprints etc,
        but sometimes applies to sanctions, it may be to applied to anything that wants to have states and transitions.

        The general idea behind this is that we are instantiating the machine object as part of the model and it will
        validate different state changes and transitions ensuring a model will be easy to identify at a certain state.

        Here we are using the pytransitions state machine in conjunction with an "action object" which is used to store
        pre-transition info, mainly the instigator of the transition or a comment about the transition.

        :param machineable: The thing (should probably a be model) that is hold the state info.
        :param state_attr: The name of the state attribute, usually `machine_state`
        """
        self.machineable = machineable
        self.__state_attr = state_attr
        self._validate_transitions(self.Transitions)

        super().__init__(
            states=[s.value for s in self.States],
            transitions=self.Transitions,
            initial=self.state,
            send_event=True,
            prepare_event=['initialize_machine'],
            ignore_invalid_triggers=True,
        )

    @property
    def state(self):
        return getattr(self.machineable, self.__state_attr)

    @state.setter
    def state(self, value):
        setattr(self.machineable, self.__state_attr, value)

    @property
    def ActionClass(self):
        raise NotImplementedError()

    def _validate_transitions(self, transitions):
        for transition in set(sum([t['after'] for t in transitions], [])):
            if not hasattr(self, transition):
                raise InvalidTransitionError(self, transition)

    def initialize_machine(self, ev):
        self.action = None
        self.from_state = ev.state

    def save_action(self, ev):
        user = ev.kwargs.get('user')
        self.action = self.ActionClass.objects.create(
            target=self.machineable,
            creator=user,
            trigger=ev.event.name,
            from_state=self.from_state.name,
            to_state=ev.state.name,
            comment=ev.kwargs.get('comment', ''),
            auto=ev.kwargs.get('auto', False),
        )

    def update_last_transitioned(self, ev):
        now = self.action.created if self.action is not None else timezone.now()
        self.machineable.date_last_transitioned = now


class ReviewsMachine(BaseMachine):
    ActionClass = ReviewAction
    States = ReviewStates
    Transitions = REVIEWABLE_TRANSITIONS

    def save_changes(self, ev):
        now = self.action.created if self.action is not None else timezone.now()
        should_publish = self.machineable.in_public_reviews_state
        if self.machineable.is_retracted:
            pass  # Do not alter published state
        elif should_publish and not self.machineable.is_published:
            if not (self.machineable.primary_file and self.machineable.primary_file.target == self.machineable):
                raise ValueError('Preprint is not a valid preprint; cannot publish.')
            if not self.machineable.provider:
                raise ValueError('Preprint provider not specified; cannot publish.')
            if not self.machineable.subjects.exists():
                raise ValueError('Preprint must have at least one subject to be published.')
            self.machineable.date_published = now
            self.machineable.is_published = True
            self.machineable.ever_public = True
        elif not should_publish and self.machineable.is_published:
            self.machineable.is_published = False
        self.machineable.save()

    def resubmission_allowed(self, ev):
        """Allow resubmission 1) if the preprint uses the PRE_MODERATION workflow, or 2) if it uses the POST_MODERATION
        workflow and is in a pending state.
        """
        workflow = self.machineable.provider.reviews_workflow
        result = any(
            [
                workflow == Workflows.PRE_MODERATION.value,
                workflow == Workflows.POST_MODERATION.value and self.machineable.machine_state == 'pending'
            ]
        )
        return result

    def perform_withdraw(self, ev):
        self.machineable.date_withdrawn = self.action.created if self.action is not None else timezone.now()
        self.machineable.withdrawal_justification = ev.kwargs.get('comment', '')

    def notify_submit(self, ev):
        user = ev.kwargs.get('user')
        notify.notify_submit(self.machineable, user)
        auth = Auth(user)
        self.machineable.add_log(
            action=PreprintLog.PUBLISHED,
            params={
                'preprint': self.machineable._id
            },
            auth=auth,
            save=False,
        )

    def notify_resubmit(self, ev):
        notify.notify_resubmit(self.machineable, ev.kwargs.get('user'), self.action)

    def notify_accept_reject(self, ev):
        notify.notify_accept_reject(self.machineable, ev.kwargs.get('user'), self.action, self.States)

    def notify_edit_comment(self, ev):
        notify.notify_edit_comment(self.machineable, ev.kwargs.get('user'), self.action)

    def notify_withdraw(self, ev):
        context = self.get_context()
        context['ever_public'] = self.machineable.ever_public
        try:
            preprint_request_action = PreprintRequestAction.objects.get(target__target__id=self.machineable.id,
                                                                   from_state='pending',
                                                                   to_state='accepted',
                                                                   trigger='accept')
            context['requester'] = preprint_request_action.target.creator
        except PreprintRequestAction.DoesNotExist:
            # If there is no preprint request action, it means the withdrawal is directly initiated by admin/moderator
            context['force_withdrawal'] = True

        for contributor in self.machineable.contributors.all():
            context['contributor'] = contributor
            if context.get('requester', None):
                context['is_requester'] = context['requester'].username == contributor.username
            mails.send_mail(
                contributor.username,
                mails.WITHDRAWAL_REQUEST_GRANTED,
                document_type=self.machineable.provider.preprint_word,
                **context
            )

    def get_context(self):
        return {
            'domain': DOMAIN,
            'reviewable': self.machineable,
            'workflow': self.machineable.provider.reviews_workflow,
            'provider_url': self.machineable.provider.domain or f'{DOMAIN}preprints/{self.machineable.provider._id}',
            'provider_contact_email': self.machineable.provider.email_contact or OSF_CONTACT_EMAIL,
            'provider_support_email': self.machineable.provider.email_support or OSF_SUPPORT_EMAIL,
        }


class NodeRequestMachine(BaseMachine):
    ActionClass = NodeRequestAction

    def save_changes(self, ev):
        """ Handles contributorship changes and state transitions
        """
        if ev.event.name == DefaultTriggers.EDIT_COMMENT.value and self.action is not None:
            self.machineable.comment = self.action.comment
        self.machineable.save()

        if ev.event.name == DefaultTriggers.ACCEPT.value:
            if not self.machineable.target.is_contributor(self.machineable.creator):
                contributor_permissions = ev.kwargs.get('permissions', self.machineable.requested_permissions)
                make_curator = self.machineable.request_type == NodeRequestTypes.INSTITUTIONAL_REQUEST.value
                visible = False if make_curator else ev.kwargs.get('visible', True)
                try:
                    self.machineable.target.add_contributor(
                        self.machineable.creator,
                        auth=Auth(ev.kwargs['user']),
                        permissions=contributor_permissions,
                        visible=visible,
                        send_email=f'{self.machineable.request_type}_request',
                        make_curator=make_curator,
                    )
                except IntegrityError as e:
                    if 'Curators cannot be made bibliographic contributors' in str(e):
                        raise Conflict(str(e)) from e
                    raise e

    def resubmission_allowed(self, ev):
        # TODO: [PRODUCT-395]
        return False

    def notify_submit(self, ev):
        """ Notify admins that someone is requesting access
        """
        context = self.get_context()
        context['contributors_url'] = f'{self.machineable.target.absolute_url}contributors/'
        context['project_settings_url'] = f'{self.machineable.target.absolute_url}settings/'
        if not self.machineable.request_type == NodeRequestTypes.INSTITUTIONAL_REQUEST.value:
            for admin in self.machineable.target.get_users_with_perm(permissions.ADMIN):
                mails.send_mail(
                    admin.username,
                    mails.ACCESS_REQUEST_SUBMITTED,
                    admin=admin,
                    osf_contact_email=OSF_CONTACT_EMAIL,
                    **context
                )

    def notify_resubmit(self, ev):
        """ Notify admins that someone is requesting access again
        """
        # TODO: [PRODUCT-395]
        raise NotImplementedError()

    def notify_accept_reject(self, ev):
        """ Notify requester that admins have approved/denied
        """
        if ev.event.name == DefaultTriggers.REJECT.value:
            context = self.get_context()
            mails.send_mail(
                self.machineable.creator.username,
                mails.ACCESS_REQUEST_DENIED,
                osf_contact_email=OSF_CONTACT_EMAIL,
                **context
            )
        else:
            # add_contributor sends approval notification email
            pass

    def notify_edit_comment(self, ev):
        """ Not presently required to notify for this event
        """
        pass

    def get_context(self):
        return {
            'node': self.machineable.target,
            'requester': self.machineable.creator
        }


class PreprintRequestMachine(BaseMachine):
    ActionClass = PreprintRequestAction

    def save_changes(self, ev):
        """ Handles preprint status changes and state transitions
        """
        if ev.event.name == DefaultTriggers.EDIT_COMMENT.value and self.action is not None:
            self.machineable.comment = self.action.comment
        elif ev.event.name == DefaultTriggers.SUBMIT.value:
            # If the provider is pre-moderated and target has not been through moderation, auto approve withdrawal
            if self.auto_approval_allowed():
                self.machineable.run_accept(user=self.machineable.creator, comment=self.machineable.comment, auto=True)
        elif ev.event.name == DefaultTriggers.ACCEPT.value:
            # If moderator accepts the withdrawal request
            self.machineable.target.run_withdraw(user=self.action.creator, comment=self.action.comment)
        self.machineable.save()

    def auto_approval_allowed(self):
        # Returns True if the provider is pre-moderated and the preprint is never public.
        return self.machineable.target.provider.reviews_workflow == Workflows.PRE_MODERATION.value and not self.machineable.target.ever_public

    def notify_submit(self, ev):
        context = self.get_context()
        if not self.auto_approval_allowed():
            reviews_signals.email_withdrawal_requests.send(timestamp=timezone.now(), context=context)

    def notify_accept_reject(self, ev):
        if ev.event.name == DefaultTriggers.REJECT.value:
            context = self.get_context()
            mails.send_mail(
                self.machineable.creator.username,
                mails.WITHDRAWAL_REQUEST_DECLINED,
                **context
            )
        else:
            pass

    def notify_edit_comment(self, ev):
        """ Not presently required to notify for this event
        """
        pass

    def notify_resubmit(self, ev):
        """ Notify moderators that someone is requesting withdrawal again
            Not presently required to notify for this event
        """
        # TODO
        pass

    def get_context(self):
        return {
            'reviewable': self.machineable.target,
            'requester': self.machineable.creator,
            'is_request_email': True,
            'document_type': self.machineable.target.provider.preprint_word
        }


class ApprovalsMachine(Machine):
    '''ApprovalsMachine manages state transitions for Sanction and SchemaResponses entities.

    The valid machine states for a Sanction object are defined in Workflows.ApprovalStates.
    The valid transitions between these states are defined in Workflows.APPROVAL_TRANSITIONS.

    The ApprovaslMachine can be used by by instantiating an ApprovalsMachine and attaching the
    desired model with the 'model' kwarg. Attached models will inherit the 'trigger' functions
    named in the APPROVAL_TRANSITIONS dictionary (submit, approve, accept, and reject).

    These trigger functions will, in order,
    1) Call any 'prepare_event' functions defined on the StateMachine (see __init__)
    2) Call Sanction member functions listed in the 'conditions' key of the dictionary
    3) Call Sanction member functions listed in the 'before' key of the dictionary
    4) Update the state field of the Sanction object via the approval_stage setter
    5) Call Sanction member functions listed in the 'after' key of the dictionary

    Attached models must define the callbacks used by the ApprvalsMachine:
    * is_moderated: Determines what transition to follow from `accept` and `reject` triggers
    * revisable: Determines what transiition to follow on a 'reject' trigger
    * `_on_submit', '_on_approve', '_on_complete', and '_on_reject': Define any custom per-trigger logic
    * _save_transition': Defines any global, post-transition logic

    If any step fails, the whole transition will fail and the Sanction's
    approval_stage will be rolled back.

    ApprovalsMachine also provides some extra functionality to  provide custom
    error messages on certain unsupported state changes.
    '''

    def __init__(self, model, active_state, state_property_name):

        super().__init__(
            model=model,
            states=ApprovalStates,
            transitions=APPROVAL_TRANSITIONS,
            initial=active_state,
            model_attribute=state_property_name,
            after_state_change='_save_transition',
            send_event=True,
            queued=True,
        )

    def get_current_state(self):
        # ApprovalsMachine should never have more than one model
        model = self.models[0]
        return self.get_model_state(model)

    def _process(self, *args, **kwargs):
        '''Wrap superclass _process to handle expected MachineErrors.'''
        try:
            super()._process(*args, **kwargs)
        except MachineError as e:
            state = self.get_current_state()
            if state in [ApprovalStates.REJECTED, ApprovalStates.MODERATOR_REJECTED]:
                error_message = (
                    'This {sanction} has already been rejected and cannot be approved'.format(
                        sanction=self.DISPLAY_NAME))
            elif state in [ApprovalStates.APPROVED, ApprovalStates.COMPLETED]:
                error_message = (
                    'This {sanction} has all required approvals and cannot be rejected'.format(
                        sanction=self.DISPLAY_NAME))
            else:
                raise e

            raise MachineError(error_message)


class CollectionSubmissionMachine(Machine):
    '''
    This is a simple state machine for Collection Submissions, removed/rejected submissions should not appear in a
    collection but should still exist in collectionsubmission_set so they can be easily resubmitted.
    '''

    def __init__(self, model, active_state, state_property_name):
        super().__init__(
            model=model,
            states=CollectionSubmissionStates,
            transitions=COLLECTION_SUBMISSION_TRANSITIONS,
            initial=active_state,
            model_attribute=state_property_name,
            after_state_change='_save_transition',
            send_event=True,
            queued=True,
        )
