from bddl.activity import evaluate_goal_conditions

from igibson.termination_conditions.termination_condition_base import BaseTerminationCondition
from igibson.utils.utils import l2_distance


class PredicateGoal(BaseTerminationCondition):
    """
    PredicateGoal used for BehaviorTask
    Episode terminates if all the predicates are satisfied
    """

    def __init__(self, config):
        super(PredicateGoal, self).__init__(config)

    def get_termination(self, task, env):
        """
        Return whether the episode should terminate.
        Terminate if point goal is reached (distance below threshold)

        :param task: task instance
        :param env: environment instance
        :return: done, info
        """
        done, _ = evaluate_goal_conditions(task.goal_conditions)
        success = done
        return done, success
