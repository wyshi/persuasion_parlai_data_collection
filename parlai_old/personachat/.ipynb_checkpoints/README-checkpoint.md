This directory contains task related to the collection of the
Persuasion for Good dataset is described in [this](https://arxiv.org/abs/1906.06725) paper.
We adopted the code from the [Persona-Chat](https://arxiv.org/pdf/1801.07243.pdf) dataset collection.

1. **personachat_chat** assumes we already have character descriptions. It randomly assigns
two Mechanical Turk workers characters, and asks them to chat to each other using that character.
2. The collected data can be found at **/ParlAI/data/personachat_chat/dilaog_pkl**. Related loading scripts also exist.
3. The survey result can be found at **/ParlAI/personachat/survey/**.