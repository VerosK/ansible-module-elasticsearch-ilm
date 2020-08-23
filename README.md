
# Ansible module Elasticsearch ILM

This repository contains Ansible module to manage ILM.


# How to use

 * create JSON document with ILM policy
 * use `elasticsearch_ilm` module from the `library` directory

   Ensure policy is defined

       - name: Ensure ilm_policy
         elasticsearch_ilm_policy:
           name: cpk-policy
           policy: "{{ lookup('template', 'templates/rollover.json.j2' ) | from_yaml | to_json }}"
           state: present

   Delete the policy

       - name: Ensure ilm_policy
         elasticsearch_ilm_policy:
           name: cpk-policy
           state: absent

## Disclaimer

This is more proof of concept than real module. It works.

If it breaks please keep both parts.

## License

CC-0. Feel free to use || abuse.  
