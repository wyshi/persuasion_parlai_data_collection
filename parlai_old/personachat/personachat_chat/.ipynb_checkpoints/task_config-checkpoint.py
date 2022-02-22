# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

task_config = {}

"""A short and descriptive title about the kind of task the HIT contains.
On the Amazon Mechanical Turk web site, the HIT title appears in search results,
and everywhere the HIT is mentioned.
"""
task_config['hit_title'] = 'Conversation about a social issue - earn up to $2! Please read the description carefully.'


"""A description includes detailed information about the kind of task the HIT contains.
On the Amazon Mechanical Turk web site, the HIT description appears in the expanded
view of search results, and in the HIT and assignment screens.
"""
task_config['hit_description'] = 'You will chat with another person while adopting a specific role. This task takes about \
                                  20 minutes and there are two short surveys for you to complete. NOTE: you are guaranteed a \
                                  base payment of $0.30 but will receive a bonus payment of $1.70 ONLY if the HIT is completed \
                                  without disconnect. This is a high risk and high reward task-- you will not \
                                  receive a bonus payment if your partner times out or disconnects. To prevent workers \
                                  from wasting time, please do not accept this HIT if you wish to quit mid-way. \
                                  '


"""One or more words or phrases that describe the HIT, separated by commas.
On MTurk website, these words are used in searches to find HITs.
"""
task_config['hit_keywords'] = 'chat, dialog, survey'


"""A detailed task description that will be shown on the HIT task preview page
and on the left side of the chat page. Supports HTML formatting.
"""
task_config['task_description'] = \
'''
<br>
<b><h3>Task Description</h3></b>
<br>
<b>In this task, you will chat with the other person regarding some social issues.
You will receive your specific conversation topic in the next stage of the description.
</b>
<br>
<br>
We will keep your conversation history to research human communication strategies.
You must exchange at least <b>10 lines each</b> for the task. There is a <b>10 min</b> time limit for each turn.
<br>
<br>
<span style="color:blue"><b>- If you believe that your task has glitched, please email us with an explanation and screenshot so that you may be paid accordingly.</b></span>
<br>
<span style="color:blue"><b>- Please contact us if you did not receive an email regarding the bonus payment after the HIT was successfully submitted.</b></span>
<br>
<span style="color:blue"><b>- You will be blocked from this HIT if we believe that your conversation is effortless. <u>(ex: replying only in CAPS, using repetitive sentences, not following instructions, and/or entering meaningless sentences to pass a chat turn)</u></b></span>
<br>
<br>
<span style="color:red">- Do not reference the task or MTurk itself during the conversation.</span>
<br>
<span style="color:red">- No racism, sexism or otherwise offensive comments, or the submission will be rejected and we will report to Amazon.</span>
'''
