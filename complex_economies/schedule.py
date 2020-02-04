# -*- coding: utf-8 -*-
from mesa.time import StagedActivation


class GroupedActivation(StagedActivation):
    def __init__(self, model, groups, stage_list=None, shuffle=False,
                 shuffle_between_stages=False, interim_functions=None):
        super().__init__(model, stage_list, shuffle, shuffle_between_stages)
        self.stage = 0
        self.groups = groups
        self.stage_functions = interim_functions

    def get_agent(self, unique_id, _raise=True):
        if _raise:
            return self._agents[unique_id]
        return self._agents.get(unique_id, None)

    def step(self):
        # we want each group to do each of their stages in order, so the outer loop is stages
        for stage in self.stage_list:
            self.stage += 1
            for group in self.groups:
                # get all agents of group
                agent_keys = [uid for uid, a in self._agents.items() if a.group == group]
                if self.shuffle:
                    self.model.random.shuffle(agent_keys)
                # run stage for each agent in group
                for agent_key in agent_keys:
                    getattr(self._agents[agent_key], stage)()
                if self.shuffle_between_stages:
                    self.model.random.shuffle(agent_keys)
                self.time += self.stage_time
            # finally, run any model level functions for that stage
            if self.stage_functions and stage in self.stage_functions:
                for func in self.stage_functions[stage]:
                    getattr(self.model, func)()
            self.time += self.stage_time

        self.steps += 1
        self.stage = 0
