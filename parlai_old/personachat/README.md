This directory contains task related to the collection of the
Persuasion for Good dataset is described in [this](https://arxiv.org/abs/1906.06725) paper.
We adopted the code from the [Persona-Chat](https://arxiv.org/pdf/1801.07243.pdf) dataset collection.

1. **personachat_chat** assumes we already have character descriptions. It randomly assigns
two Mechanical Turk workers characters, and asks them to chat to each other using that character.
2. The collected data can be found at **/ParlAI/data/personachat_chat/dilaog_pkl**. Related loading scripts also exist.
3. The survey result can be found at **/ParlAI/personachat/survey/**.

Data Collection:

To launch a mturk task using this package simply execute run.py in the personachat_chat folder. 
Task configurations can be adjusted from the command line, below are some descriptions for useful command line arguments.
For a full list of command line options see run.py and parlai/core/params.py

-nc:           Number of conversations, default = 1

--unique:      Enforce that no worker can work on your task twice

-r:            Reward for each worker for finishing the conversation, default = .05

--live:        Submit the HITs to MTurk live site, launches to the mturk sandbox by default

-rt:           Minimum number of turns that must pass before the chat can be completed, default = 10

The number of hits that will launch is equal to num_conversations * num_agents_per_convo * 1.5.
This task involves two agents so num_agents_per_convo will always be 2. 
The default mturk hit multiplier is 1.5 and is used to ensure worker availibility see parlai/mturk/core/mturk_manager.py for more details.

Examples:

Run a task live with 3 conversations, a reward of $0.10, and with conversations having a min of 5 turns

python run.py --live -r=.1 -rt=5

Task configurations will print to the screen when executing run.py.