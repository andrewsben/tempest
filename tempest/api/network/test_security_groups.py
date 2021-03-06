# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.api.network import base_security_groups as base
from tempest import test


class SecGroupTest(base.BaseSecGroupTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecGroupTest, cls).setUpClass()
        if not test.is_extension_enabled('security-group', 'network'):
            msg = "security-group extension not enabled."
            raise cls.skipException(msg)

    @test.attr(type='smoke')
    def test_list_security_groups(self):
        # Verify the that security group belonging to tenant exist in list
        resp, body = self.client.list_security_groups()
        self.assertEqual('200', resp['status'])
        security_groups = body['security_groups']
        found = None
        for n in security_groups:
            if (n['name'] == 'default'):
                found = n['id']
        msg = "Security-group list doesn't contain default security-group"
        self.assertIsNotNone(found, msg)

    @test.attr(type='smoke')
    def test_create_show_delete_security_group(self):
        group_create_body, name = self._create_security_group()

        # Show details of the created security group
        resp, show_body = self.client.show_security_group(
            group_create_body['security_group']['id'])
        self.assertEqual('200', resp['status'])
        self.assertEqual(show_body['security_group']['name'], name)

        # List security groups and verify if created group is there in response
        resp, list_body = self.client.list_security_groups()
        self.assertEqual('200', resp['status'])
        secgroup_list = list()
        for secgroup in list_body['security_groups']:
            secgroup_list.append(secgroup['id'])
        self.assertIn(group_create_body['security_group']['id'], secgroup_list)

    @test.attr(type='smoke')
    def test_create_show_delete_security_group_rule(self):
        group_create_body, _ = self._create_security_group()

        # Create rules for each protocol
        protocols = ['tcp', 'udp', 'icmp']
        for protocol in protocols:
            resp, rule_create_body = self.client.create_security_group_rule(
                group_create_body['security_group']['id'],
                protocol=protocol
            )
            self.assertEqual('201', resp['status'])
            self.addCleanup(self._delete_security_group_rule,
                            rule_create_body['security_group_rule']['id']
                            )

        # Show details of the created security rule
        resp, show_rule_body = self.client.show_security_group_rule(
            rule_create_body['security_group_rule']['id']
        )
        self.assertEqual('200', resp['status'])

        # List rules and verify created rule is in response
        resp, rule_list_body = self.client.list_security_group_rules()
        self.assertEqual('200', resp['status'])
        rule_list = [rule['id']
                     for rule in rule_list_body['security_group_rules']]
        self.assertIn(rule_create_body['security_group_rule']['id'], rule_list)

    @test.attr(type='smoke')
    def test_create_security_group_rule_with_additional_args(self):
        # Verify creating security group rule with the following
        # arguments works: "protocol": "tcp", "port_range_max": 77,
        # "port_range_min": 77, "direction":"ingress".
        group_create_body, _ = self._create_security_group()

        direction = 'ingress'
        protocol = 'tcp'
        port_range_min = 77
        port_range_max = 77
        resp, rule_create_body = self.client.create_security_group_rule(
            group_create_body['security_group']['id'],
            direction=direction,
            protocol=protocol,
            port_range_min=port_range_min,
            port_range_max=port_range_max
        )

        self.assertEqual('201', resp['status'])
        sec_group_rule = rule_create_body['security_group_rule']
        self.addCleanup(self._delete_security_group_rule,
                        sec_group_rule['id']
                        )

        self.assertEqual(sec_group_rule['direction'], direction)
        self.assertEqual(sec_group_rule['protocol'], protocol)
        self.assertEqual(int(sec_group_rule['port_range_min']), port_range_min)
        self.assertEqual(int(sec_group_rule['port_range_max']), port_range_max)


class SecGroupTestXML(SecGroupTest):
    _interface = 'xml'
