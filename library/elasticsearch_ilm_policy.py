from __future__ import absolute_import

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import json


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type="str"),
            policy=dict(required=False, default=None),
            state=dict(default="present", choices=["present", "absent"]),
            force=dict(default=True, type=bool),
            timeout=dict(default="1m"),
            elasticsearch_host=dict(type="str",
                                    default="http://localhost:9200")
        ),
        supports_check_mode=True
    )

    policy_name = module.params["name"]
    target_state = module.params["state"]
    target_policy_document = module.params["policy"]
    elasticsearch_host = module.params["elasticsearch_host"]
    if elasticsearch_host[-1] == '/':
        elasticsearch_host = elasticsearch_host[:-1]

    # Make sure policy is dictionary
    if target_state == 'present':
        if type(target_policy_document) in [str, bytes]:
            target_policy_document = json.loads(target_policy_document)
        if type(target_policy_document) != dict:
            module.fail_json(changed=False,
                             msg="Policy document has to be valid dictionary. Got {}".format(
                                 type(target_policy_document)),
                             policy_document=target_policy_document)

    # Get the current ILM policy
    is_present, current_policy_json = False, None
    response, info = fetch_url(module,
                               url="{}/_ilm/policy/{}".format(
                                   elasticsearch_host, policy_name
                               ))
    if info['status'] == 404:
        is_present = False
    if info['status'] == 200:
        is_present = True
    assert response.headers
    _policy = json.loads(response.read())
    current_policy_document = _policy[policy_name]
    if info['status'] not in [200, 404]:
        return module.fail_json(msg="Unable to check policy",
                                policy_name=policy_name)

    # Check whether we need to get change the policy
    change_required = False
    target_policy_json = json.dumps(target_policy_document)
    if is_present and target_state == 'absent':
        change_required = True
        change_msg = "Removing policy {}".format(policy_name)
    elif is_present and target_state == 'absent':
        change_required = True
        change_msg = "Creating policy {}".format(policy_name)
    elif is_present and target_state == 'present':
        policy_to_check = current_policy_document
        # remove policy fields created by ES
        if 'modified_date' not in target_policy_document:
            del policy_to_check['modified_date']
        if 'version' not in target_policy_document:
            del policy_to_check['version']
        #
        if policy_to_check != target_policy_document:
            change_required = True
            change_msg = "Updating policy {}".format(policy_name)

    # on no change required, exit
    if not change_required:
        module.exit_json(changed=False, policy_name=policy_name,
                         msg="No change required")

    # on change required, stop here (in check mode only)
    if change_required and module.check_mode:
        module.exit_json(changed=True, policy_name=policy_name,
                         msg=change_msg,
                         policy=target_policy_document,
                         old_policy=current_policy_document,
                         )
    #
    assert change_required

    if target_state == 'absent':
        response, info = fetch_url(
            module=module,
            method='DELETE',
            url='{}/_ilm/policy/{}'.format(elasticsearch_host, policy_name))

        assert info['status'] == 200
        module.exit_json(changed=True,
                         policy_name=policy_name,
                         msg="Policy removed",
                         old_policy=current_policy_json,
                         )
    #
    assert target_state == 'present'

    response, info = fetch_url(
        module=module,
        method='PUT',
        url='{}/_ilm/policy/{}'.format(elasticsearch_host, policy_name),
        headers={"Content-type": 'application/json'},
        data=target_policy_json
    )


    if info['status'] != 200:
        module.exit_json(changed=True,
                         policy_name=policy_name,
                         msg="Error during policy update. Expected status 200",
                         info = info,
                         status=info['status'],
                         data=target_policy_json,
                         )

    module.exit_json(changed=True,
                     policy_name=policy_name,
                     msg="Policy updated",
                     policy=target_policy_document,
                     old_policy=current_policy_document,
                     )


if __name__ == '__main__':
    main()
