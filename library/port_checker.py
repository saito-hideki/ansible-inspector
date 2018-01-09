#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Hideki Saito <saito@fgrep.org>
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import socket
import time
from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: port_checker
author:
    - Hideki Saito (@saito-hideki)
version_added: "2.4"
short_description: TCP port checker
description:
    - Check whether listed ports are opened.
options:
    host:
        description:
            - The name or IPAddress of target host to check port.
        required: true
    ports:
        description:
            - The integer value list of port numbers.
        required: true
        type: list
    interval:
        description:
            - The integer value of the check interval (seconds).
            - Each port is checked every seconds specified here.
        required: false
        type: int
        default: 5
    retries:
        description:
            - The integer value of the retry count.
            - If the port check failed, it will retry for the specified number
              of counts.
        required: false
        type: int
        default: 3
    state:
        description:
            - Specified C(opened) or C(closed), it will confirm the port.
        choices: [ opened, closed ]
        required: true
'''

EXAMPLES = '''
# Checking service ports are opened
- port_checker:
    host: 192.168.100.100
    ports:
      - 22
      - 80
      - 443
    state: opened

# Checking service ports are closed
- port_checker:
    host: 192.168.100.100
    ports:
      - 10080
      - 10443
    interval: 10
    retries: 5
    state: closed
'''

MOD_DRYRUN = 'dryrun'
MOD_OPENED = 'opened'
MOD_CLOSED = 'closed'


def _check_port_open(host, port, interval, retries):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for retry in range(retries):
        try:
            sock.connect((host, port))
            sock.close()
            return True
        except socket.error as err:
            time.sleep(interval)
    sock.close()
    return False


def _check_port_list(module_params):
    ports_state = dict(opened=list(), closed=list())
    for port in module_params['ports']:
        state = _check_port_open(module_params['host'],
                                 port,
                                 module_params['interval'],
                                 module_params['retries'])
        if state:
            ports_state['opened'].append(port)
        else:
            ports_state['closed'].append(port)
    return ports_state


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        host=dict(type='str', required=True),
        ports=dict(type='list', require=True),
        state=dict(type='str', choices=['opened', 'closed']),
        interval=dict(type='int', required=False, default=5),
        retries=dict(type='int', required=False, default=3)
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # initialize the module_params that will use for the result
    module_params = dict(
        host=module.params['host'],
        ports=module.params['ports'],
        state=module.params['state'],
        interval=module.params['interval'],
        retries=module.params['retries']
    )

    # seed the result dict in the object
    result = dict(
        changed=False,
        checker_mode='',
        checker_status=dict()
    )

    # initialize the the AnsibleModule object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        result['checker_mode'] = MOD_DRYRUN
        module.exit_json(**result)

    # checking specified port
    # if state is opened, when all ports are opened -> task will be succeeded
    # if state is closed, when all ports are closed -> task will be succeeded
    result['checker_status'] = _check_port_list(module_params)
    if module_params['state'] == 'opened':
        result['checker_mode'] = MOD_OPENED
        ports = result['checker_status']['closed']
        if len(ports) > 0:
            module.fail_json(
                msg='specified ports are closed: %s' % ','.join(
                    [str(p) for p in ports]
                )
            )
    elif module_params['state'] == 'closed':
        result['checker_mode'] = MOD_CLOSED
        ports = result['checker_status']['opened']
        if len(ports) > 0:
            module.fail_json(
                msg='specified ports are opened: %s' % ','.join(
                    [str(p) for p in ports]
                )
            )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
