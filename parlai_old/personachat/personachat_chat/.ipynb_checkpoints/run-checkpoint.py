# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
from parlai.core.params import ParlaiParser
from parlai.mturk.core.mturk_manager import MTurkManager
from worlds import \
    PersonaChatWorld, PersonaProfileWorld, PersonasGenerator
from task_config import task_config
import sys
import torch
import os


def main():
    """This task consists of one agent, model or MTurk worker, talking to an
    MTurk worker to negotiate a deal.
    """
    argparser = ParlaiParser(False, False)
    argparser.add_parlai_data_path()
    argparser.add_mturk_args()
    argparser.add_argument('-min_t', '--min_turns', default=10, type=int,
                           help='minimum number of turns')
    argparser.add_argument('-mt', '--max_turns', default=50, type=int,
                           help='maximal number of chat turns')
    argparser.add_argument('-mx_rsp_time', '--max_resp_time', default=600,
                           type=int,
                           help='time limit for entering a dialog message')
    argparser.add_argument('-mx_psn_time', '--max_persona_time', type=int,
                           default=3600, help='time limit for turker'
                           'entering the persona')
    argparser.add_argument('--ag_shutdown_time', default=600,
                           type=int,
                           help='time limit for entering a dialog message')
    argparser.add_argument('--persona-type', default='both', type=str,
                           choices=['both', 'self', 'other'],
                           help='Which personas to load from personachat')
    argparser.add_argument('--revised', default=False, type='bool',
                           help='Whether to use revised personas')
    argparser.add_argument('-rt', '--range_turn', default='10',
                           help='sample range of number of turns')
    argparser.add_argument('--personas-path', default=None,
                           help='specify path for personas data')
    opt = argparser.parse_args()

    directory_path = os.path.dirname(os.path.abspath(__file__))
    opt['task'] = os.path.basename(directory_path)

    if not opt.get('personas_path'):
        opt['personas_path'] = argparser.parlai_home + '/parlai/mturk/personachat_chat/data'

    opt.update(task_config)

    opt['extract_personas_path'] = os.path.join(opt['datapath'], 'personachat_chat')

    mturk_agent_ids = ['PERSON_1', 'PERSON_2']

    mturk_manager = MTurkManager(
        opt=opt,
        mturk_agent_ids=mturk_agent_ids
    )

    persona_generator = PersonasGenerator(opt)
    mturk_manager.setup_server(task_directory_path=directory_path)

    try:
        mturk_manager.start_new_run()
        agent_qualifications = [
        {
            'QualificationTypeId': "000000000000000000L0", # PercentAssignmentsApproved
            'Comparator': 'GreaterThan',
            'IntegerValues':[95]
        },
        {
            'QualificationTypeId' : "00000000000000000071",  # Worker Location
            'Comparator' : 'EqualTo',
            'LocaleValues' : [{
          		'Country' : "US"
        	}]
        }
        ]

        mturk_manager.create_hits(qualifications=agent_qualifications)

        if not opt['is_sandbox']:
            blocked_worker_list = ['ABZ1LM3J8REE6', 'A1H5PLHJUV3RIO', 'A324AD5U1SV0OA', 'A136AGQ0VJPGST', 'A1KEAHVVML6319', 'A26FIQ42LD6QIO',
                                    'A2MM10557W7PLD', 'A1LA81KYK6626F', 'A2QQE2ZP8NSRKX', 'AEWE62WB242HX', 'A1BVEXQ684HDEP', 'A3CHSKOAWR1DVA',
                                    'A7E03QY7B281X', 'A3E2NEZ6M1N1DT', 'A2J9ZWDTAFJW65', 'AK11BPNWE727G', 'A8UI77795LTGF', 'A3I72FPW52ABJ5',
                                    'A3FPPZWMQOANR4', 'A3HBD7WXNMEWVO'
            ] # block workers
            for w in blocked_worker_list:
                mturk_manager.block_worker(w, 'We found that you have unexpected behaviors in our previous HITs. For more questions please email us.')

        def run_onboard(worker):
            worker.persona_generator = persona_generator
            world = PersonaProfileWorld(opt, worker)
            world.parley()
            world.shutdown()
        mturk_manager.set_onboard_function(onboard_function=run_onboard)
        mturk_manager.ready_to_accept_workers()

        def check_worker_eligibility(worker):
            return True

        def assign_worker_roles(workers):
            for index, worker in enumerate(workers):
                worker.id = mturk_agent_ids[index % len(mturk_agent_ids)]

        def run_conversation(mturk_manager, opt, workers):
            agents = [workers[0], workers[1]]
            conv_idx = mturk_manager.conversation_index
            world = PersonaChatWorld(
                opt=opt,
                agents=agents,
                range_turn=[int(s) for s in opt['range_turn'].split(',')],
                max_turn=opt['max_turns'],
                max_resp_time=opt['max_resp_time'],
                world_tag='conversation t_{}'.format(conv_idx)
            )
            world.reset_random()

            while not world.episode_done():
                world.parley()

            world.save_data()
            world.shutdown()

            # Pay bonus
            if (world.convo_is_finished is True):
                for ag in agents:
                    if (ag.hit_is_complete):
                        print("Completed the task successfully, paying bonus to", ag.worker_id)
                        mturk_manager.pay_bonus(ag.worker_id, 1.7, ag.assignment_id, "Completed the task successfully!", ag.assignment_id)
            else:
                print("Did not complete the task. No bonus paid.")

            world.review_work()

        mturk_manager.start_task(
            eligibility_function=check_worker_eligibility,
            assign_role_function=assign_worker_roles,
            task_function=run_conversation
        )

    except BaseException:
        raise
    finally:
        mturk_manager.expire_all_unassigned_hits()
        mturk_manager.shutdown()


if __name__ == '__main__':
  
    

    main()
