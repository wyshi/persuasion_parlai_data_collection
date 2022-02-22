# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
from parlai.core.agents import create_agent
from parlai.mturk.core.worlds import MTurkOnboardWorld
from parlai.mturk.core.agents import TIMEOUT_MESSAGE
from parlai.core.agents import create_agent
from parlai.core.worlds import validate, MultiAgentDialogWorld
from joblib import Parallel, delayed
from extract_and_save_personas import main as main_extract
import numpy as np
import time
import os
import pickle
import random
import math
import csv
pathname = os.path.dirname(os.getcwd())
ID_PATH = pathname+'/user_id'
SURVEY_PATH= pathname+ '/survey'
DATA_DIR_PATH = '/dialogs_pkl'

TIMEOUT_MSG = '<b> The other person has timed out. \
        Please click the "Done with this HIT" button below to finish this HIT.\
        </b>'
WAITING_MSG = 'Please wait while we match you with another worker...'

class PersonasGenerator(object):
    def __init__(self, opt):
        self.personas_idx_stack_path = os.path.join(opt['extract_personas_path'],
                                                    './personas_idx_stack.pkl')

        self.personas_path = '{}/personas-{}'.format(
                             opt['extract_personas_path'],
                             opt['persona_type'] +
                                'Revised' if opt['revised'] else 'Original')

        if not os.path.exists(self.personas_path):
            opt['personas_path'] = self.personas_path
            main_extract(opt)
        self.personas_name_list = []

        for f_name in os.listdir(self.personas_path):
            if f_name.endswith('.pkl'):
                self.personas_name_list.append(f_name)

        if os.path.exists(self.personas_idx_stack_path):
            with open(self.personas_idx_stack_path, 'rb') as handle:
                self.idx_stack = pickle.load(handle)
        else:
            self.idx_stack = []
            self.add_idx_stack()
            self.save_idx_stack()
        pass

    def add_idx_stack(self):
        stack = [i for i in range(len(self.personas_name_list))]
        self.idx_stack = stack + self.idx_stack

    def pop_persona(self):
        if len(self.idx_stack) == 0:
            self.add_idx_stack()
        data='Unused'
        idx=0
        return (idx, data)

    def push_persona(self, idx):
        self.idx_stack.append(idx)

    def save_idx_stack(self):
        pass

class PersonaProfileWorld(MTurkOnboardWorld):
    """A world that provides a persona to the MTurkAgent"""
    def __init__(self, opt, mturk_agent):
        self.task_type = 'sandbox' if opt['is_sandbox'] else 'live'
        self.max_persona_time = opt['max_persona_time']
        super().__init__(opt, mturk_agent)

    def parley(self):
        persona_idx, data = self.mturk_agent.persona_generator.pop_persona()
        self.mturk_agent.persona_idx = persona_idx
        self.mturk_agent.persona_data = data
        persona_text = "Welcome to the communication task. You will now start a conversation with your partner about a childre's charity. If you are asked to donate, you can choose any amount from $0 to all your payment ($2). Please don't game the task by replying short and meaningless sentences-- you will be reported and blocked."
        self.mturk_agent.observe({
            'id': 'SYSTEM',
            'show_persona': True,
            'text': '<br>' + persona_text + '<br>'})

        act = self.mturk_agent.act(timeout=self.max_persona_time)

        # Save pre-task survey to file
        if 'worker_id' in act:
            fields = [act['worker_id']]
            for pre in act['pre_task_survey']:
                fields.append(act['pre_task_survey'][pre])
            data_path = DATA_DIR_PATH
            with open(os.path.join(SURVEY_PATH,'pre_task_survey.csv'), 'a') as f:
                writer = csv.writer(f)
                writer.writerow(fields)
        # timeout
        if act['episode_done'] or (('text' in act and
                                    act['text'] == TIMEOUT_MESSAGE)):

            self.mturk_agent.persona_generator.push_persona(
                self.mturk_agent.persona_idx)
            self.mturk_agent.persona_generator.save_idx_stack()
            self.episodeDone = True
            return

        if 'text' not in act:
            control_msg = {'id': 'SYSTEM',
                           'text': WAITING_MSG}
            self.mturk_agent.observe(validate(control_msg))
            self.episodeDone = True


class PersonaChatWorld(MultiAgentDialogWorld):
    def __init__(self, opt, agents=None, shared=None,
                 range_turn=10, max_turn=50,
                 max_resp_time=600,
                 world_tag='NONE',
                 agent_timeout_shutdown=600):
        self.agents = agents
        self.turn_idx = 0
        self.range_turn = range_turn
        self.max_turn = max_turn
        self.n_turn = self.range_turn
        self.dialog = []
        self.task_type = 'sandbox' if opt['is_sandbox'] else 'live'
        self.chat_done = False
        self.donation_done = False
        self.world_tag = world_tag
        self.persuader_donation = -1
        self.persuadee_donation = -1
        self.convo_is_finished = False

        # below are timeout protocols
        self.max_resp_time = max_resp_time # in secs
        self.agent_timeout_shutdown = agent_timeout_shutdown
        super().__init__(opt, agents, shared)

        # get personas
        self.personas = [(ag.persona_data if hasattr(ag, 'persona_data') else None) for ag in self.agents]

        # save mturk id
       
        if not os.path.exists(ID_PATH):
            os.makedirs(ID_PATH)

        fp1 = open(ID_PATH + 'persuader_ids.txt', 'a')
        fp1.write(str(self.agents[0].worker_id) + '\n')
        fp1.close()

        fp2 = open(ID_PATH + 'persuadee_ids.txt', 'a')
        fp2.write(str(self.agents[1].worker_id) + '\n')
        fp2.close()

    def parley(self):
        self.turn_idx += 1

        print(self.world_tag + ' is at turn {}...'.format(self.turn_idx))

        control_msg = {'episode_done': False}
        control_msg['id'] = 'SYSTEM'

        """If at first turn, we need to give each agent their persona"""
        if self.turn_idx == 1:
            for idx, agent in enumerate(self.agents):
                control_msg['persona_text'] = self.get_instruction(
                                            tag='identity',
                                            agent_id=agent.id)
                control_msg['text'] = self.get_instruction(
                                            tag='start',
                                            agent_id=agent.id)
                agent.observe(validate(control_msg))
                if idx == 0:
                    time.sleep(3)

        """If we get to the min turns, inform turker that they can end if they
           want
        """
        if self.turn_idx == self.n_turn + 1:
            for idx, agent in enumerate(self.agents):
                control_msg['text'] = self.get_instruction(idx, tag='exceed_min_turns')
                control_msg['exceed_min_turns'] = True
                agent.observe(validate(control_msg))

        """Otherwise, we proceed accordingly"""
        acts = [None, None]
        for idx, agent in enumerate(self.agents):
            if self.donation_done: # get donation value from both agents
                for ag in self.agents:
                    acts[idx] = ag.act() # taking post-survey and entering donation amount
                    if acts[idx]['episode_done'] == False:
                        acts[idx] = ag.act(timeout=self.max_resp_time)
                    if acts[idx]['id'] == 'PERSON_1' and 'donation_value' in acts[idx]:
                        self.persuader_donation = acts[idx]['donation_value']
                    elif acts[idx]['id'] == 'PERSON_2' and 'donation_value' in acts[idx]:
                        self.persuadee_donation = acts[idx]['donation_value']
                    self.chat_done = True
                    # Save post-task survey to file
                    if 'worker_id' in acts[idx]:
                        fields = [acts[idx]['worker_id']]
                        for post in acts[idx]['post_task_survey']:
                            fields.append(acts[idx]['post_task_survey'][post])
                        with open(os.path.join(SURVEY_PATH,'post_task_survey.csv'), 'a') as f:
                            writer = csv.writer(f)
                            writer.writerow(fields)

            if not self.chat_done:
                acts[idx] = agent.act(timeout=self.max_resp_time)

            if self.check_timeout(acts[idx]):
                return

            if self.turn_idx > 1:
                # only check on first message
                while self.is_msg_tooshortlong(acts[idx], agent):
                    acts[idx] = agent.act(timeout=self.max_resp_time)

            # after an agent clicks the "Done" button
            if (acts[idx]['donation_done'] == True):
                self.donation_done = True
                for ag in self.agents:
                    control_msg['text'] = 'One of you ended the chat. Please take the survey and indicate how much you would like to donate out of \
                                           your payment in the donation tab below.'
                    control_msg['donation_done'] = True
                    ag.observe(validate(control_msg))

            if acts[idx]['episode_done'] == True:
                self.n_turn = self.turn_idx - 1
                self.chat_done = True
                for ag in self.agents:
                    # if agent disconnected
                    if ag != agent and ag.some_agent_disconnected:
                        control_msg['text'] = 'The other worker unexpectedly disconnected. You will be compensated. \
                                               Please click "Done with this HIT" button below to finish this HIT.'
                        control_msg['episode_done'] = True
                        ag.observe(validate(control_msg))
                        return
                return
            else:
                self.dialog.append((idx, acts[idx]['text']))
                for other_agent in self.agents:
                    if other_agent != agent:
                        other_agent.observe(validate(acts[idx]))

    def shutdown(self):
        global shutdown_agent
        def shutdown_agent(mturk_agent):
            mturk_agent.shutdown(mturk_agent)
        Parallel(
            n_jobs=len(self.agents),
            backend='threading'
        )(delayed(shutdown_agent)(agent) for agent in self.agents)


    def episode_done(self):
        return self.chat_done

    def get_instruction(self, agent_id=None, tag='first'):
        # assign roles based on which Turker connects first and second via agent_id
        if tag == 'identity':
            if (agent_id == 'PERSON_1'):
                persona_text = "You are randomly assigned to be the <span style=\"font-size: 20px;\"><b><i>Persuader</i></b></span> in this communication task.<br><br>As the persuader, your job is to persuade your partner to <span style=\"text-decoration: underline;\">donate <b>some or all</b> of his/her incoming payment for this task</span> to a children’s charity called <span style=\"color:red\">Save the Children</span>.<br><br> If you succeed in persuading your partner to donate, you will be paid an <b>extra</b> of whatever your partner decides to donate to the charity (you keep the money) OR you can decide to donate your extra gain to <span style=\"color:red\">Save the Children</span> directly to maximize the help! You are not allowed to tell the persuadee your goal or collude with the persuadee.<br><br>You have to ask your partner to give a specific amount of donation out of his/her task payment. By the end of the conversation, you have to ask questions like <b>\"How much do you like to donate to the charity now? Your donation will be directly deducted from your task payment. You can choose any amount from $0 to all your payment ($2).\"</b> If the partner asks you how this donation will get to the charity, you can simply answer, \"The research team will collect all donations and send it to <span style=\"color:red\">Save the Children</span>.\"<br><br>Please lead the conversation by being aware of the 10 minimum chat turns. Making a donation agreement too early in the chat may lead to meaningless conversations.<br><br><b><span style=\"color:#2e75b5; font-size:20px;\">Your \"Magical Persuasion Toolkit\"</span></b><br><br><span style=\"color:red\">Basic information about Save the Children:</span><br><br><span style=\"color:red\">Save the Children</span> is an international non-governmental organization that promotes children's rights, provides relief and helps support children in developing countries.<br><br>There are several ways to organize our messages to enhance your persuasion skills:<br><br><ul><li><b><u>Use logical appeal: You can persuade by using logical arguments.</b></u> You can basically tell your partner what <span style=\"color:red\">Save the Children</span> is and how their donation is essential to help ensuring children’s rights to health, education, safety, etc. Convince your partner their donation will make a tangible impact for the world. <b><u>Try to use statistics and evidence to support your argument.</b></u></li><li><b>Use emotional appeal: You can persuade by using emotions.</b>  You can tell a story of a child who died from hunger and how their donation will help individual children and their families. <b><u>Try to use personal stories to involve your partner.</b></u></li><li><b>Use credibility appeal: You can persuade by using credibility appeals.</b> You can tell how good and professional <span style=\"color:red\">Save the Children</span> is. Mention the organization’s credentials and international impact. <b><u>Convince your partner to believe their donation will go to a trustable fund.</b></u></li><li><b>Use anger appeal: You can persuade by making your partner angry.</b>  You can inform your partner about a lack of support for children in developing countries, especially in war zones. For instance, millions of Syrian children have grown up facing the daily threat of violence. In the first two months of 2018 alone, 1,000 children were reportedly killed or injured in intensifying violence. Convince your partner their donation can address such problems. <b><u>Convince your partner that they should be angry and should do something.</b></u></li><li><b>Use guilt appeal: You can persuade by making your partner guilty.</b> You can ask how much money do they spend on unnecessary stuff like a bag of snack or candy… and remind them that money can be used in more meaningful ways. Small donations will indeed help a lot of children and their families. <b><u>Convince your partner they are a part of the solution and they have the moral responsibility to help.</b></u></li></ul><br><br>You can refer to <span style=\"color:red\">Save the Children</span>’s website to gather more information if you like to.<br><br><a href=\"https://www.savethechildren.org/\" target=\"_blank\">https://www.savethechildren.org/</a>"
                return persona_text
            else:
                persona_text = "Welcome to the communication task. You will now start a conversation with your partner \
                                about a children’s charity. If you are asked to donate, you can choose any amount from $0 to all your payment ($2). \
                                Please don’t game the task by replying short and meaningless sentences-- you will be reported and blocked."
                return persona_text

        if tag == 'start':
            return '\nSuccessfully matched! \n\
                    You need to finish at least <b>' + str(self.n_turn) + ' chat turns each</b> to end the chat. There is a <b>10 min</b> time limit for each turn. \n \
                    <span style="color:blue"><b> We encourage you to keep the conversation until a donation agreement is explicitly made.</b></span> \n \
                    <b>You can track your communicator role description on the left panel.</b>'

        if tag == 'chat_not_done':
            return 'Sorry, we need at least <b>' + str(self.n_turn - self.turn_idx) + ' more turn(s)</b> to finish. ' + \
                   'Please send a new message:'

        if tag == 'timeout':
            return '<b>{}</b> is timeout. \
                    Please click the "Done with this HIT" button below to exit this HIT. No rejections.'.format(agent_id)

        if tag == 'exceed_min_turns':
            return '\n {} chat turns finished! \n Keep chatting or you can click the "Done" button to end the chat if it\'s your turn. \n \
                    <span style="color:blue"><b>We encourage you to keep the conversation until a donation agreement is explicitly made.</b></span>'.format(self.n_turn)

    def save_data(self):
        convo_finished = True
        bad_workers = []
        for ag in self.agents:
            if (ag.hit_is_abandoned or ag.hit_is_returned or \
                ag.disconnected or ag.hit_is_expired):
                bad_workers.append(ag.worker_id)
                convo_finished = False
        if not convo_finished or self.dialog == []:
            for ag in self.agents:
                ag.not_approve = True
                ag.persona_generator.push_persona(ag.persona_idx)

        data_path = self.opt['extract_personas_path'] + DATA_DIR_PATH
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        if convo_finished:
            filename = os.path.join(data_path, '{}_{}_{}.pkl'.format(time.strftime("%Y%m%d-%H%M%S"), np.random.randint(0, 1000), self.task_type))
            self.convo_is_finished = True
        else:
            filename = os.path.join(data_path, '{}_{}_{}_incomplete.pkl'.format(time.strftime("%Y%m%d-%H%M%S"), np.random.randint(0, 1000), self.task_type))
        print(self.world_tag+': Data successfully saved at {}.'.format(filename))
        print(self.dialog)
        pickle.dump({'personas': self.personas,
                     'dialog': self.dialog,
                     'workers': [ag.worker_id for ag in self.agents],
                     'bad_workers': bad_workers,
                     'n_turn': self.n_turn,
                     'persuader_donation': self.persuader_donation,
                     'persuadee_donation': self.persuadee_donation},
                     open(filename, 'wb'))

    def is_msg_tooshortlong(self, act, ag, th_min=3, th_max=100):
        if act['episode_done'] == True:
            return False

        control_msg = {'episode_done': False}
        control_msg['id'] = 'SYSTEM'

        msg_len = len(act['text'].split(' '))
        if msg_len < th_min:
            control_msg['text'] = 'Your message is too short, please make it more than <b><span style="color:red">3 words</span></b>.'
            ag.observe(validate(control_msg))
            return True
        if msg_len > th_max:
            control_msg['text'] = 'Your message is too long, please make it less than <b><span style="color:red">100 words</span></b>.'
            ag.observe(validate(control_msg))
            return True
        return False

    def reset_random(self):
        self.n_turn = self.range_turn[0]

    def check_timeout(self, act):
        if act['text'] == '[TIMEOUT]' and act['episode_done'] == True:
            control_msg = {'episode_done': True}
            control_msg['id'] = 'SYSTEM'
            control_msg['text'] = self.get_instruction(agent_id=act['id'], tag='timeout')
            for ag in self.agents:
                if ag.id != act['id']:
                    ag.observe(validate(control_msg))
            self.chat_done = True
            return True
        else:
            return False

    def review_work(self):
        global review_agent
        def review_agent(ag):
            if hasattr(ag, 'not_approve'):
                pass
            else:
                ag.approve_work()
        Parallel(n_jobs=len(self.agents), backend='threading')(delayed(review_agent)(agent) for agent in self.agents)

if __name__ == '__main__':
    app.run(debug=True)
