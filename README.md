# Ansible Tower Splunk Framework

This repo contains the Framework for the Ansible Tower Splunk App.

Data analysis and visualization of Ansible Tower jobs in Splunk

### Background ###

Many Ansible customers use Splunk to capture, analyze, and report on data from all aspects of their enterprise IT infrastructure. These users would benefit from a deeper integration that would allow them to run Splunk queries on playbook runtime data retrieved via the Ansible Tower rest API.

### Problem / Use Cases ###

The existing audit functionality in Ansible Tower does not allow customers to generate reports. Additionally, Tower does not currently have the ability to provide advanced analytics on this data including:

* Automatically flagging changes to a fact (i.e. system) (something changed)
* Learning normal, reporting weird (compliance)
* Searching for specific fact values across N systems (finding the needle in a haystack)
* Removing systems from Tower inventory removes system tracking details (persistence and auditing)
* Rapidly comparing N systems (compliance, scalability)
* Reporting on facts across systems
* Analysis by providing richer details on job events.

### Solution ###

The Splunk integration will specifically target the following use cases:

#### Run Splunk Queries on Tower Activity Stream ####

Tower users will be able to run queries Activity Stream information. The set of data targeted includes a full job output, which includes all job details, activity streams and service logs.

The Activity Stream data to be retrieved includes the following fields:

* Name: The name of the job template from which this job was launched.
* Status: Can be any of Pending, Running, Successful, or Failed.
* License Error: Only shown for Inventory Sync jobs. If this is True, the hosts added by the
inventory sync caused Tower to exceed the licensed number of managed hosts.
* Started: The timestamp of when the job was initiated by Tower.
* Finished: The timestamp of when the job was completed.
* Elapsed: The total time the job took.
* Launch Type: Manual or Scheduled.
* Standard Out: Shows the full results of running the SCM Update or Inventory Sync playbook. Same information you would see if you ran the Ansible playbook using Ansible from the command line.
* Credential: The cloud credential for the job
* Group: The group being synced
* Source: The type of cloud inventory
* Regions: Any region filter, if set
* Overwrite: The value of Overwrite for this Inventory Sync. Refer to Inventories for details.
* Overwrite Vars: The value of Overwrite Vars for this Inventory Sync. Refer to Inventories for details.

#### Run Splunk Queries on System Tracking ####

Tower users will be able to run queries against System Tracking data. The set of data to be targeted includes services, packages and hardware data.

This data will give Tower users the ability to audit and verify that machines are in compliance, see how a machine has changed over time, or compare machines in an environment to see how they differ from each other.

#### Run Splunk Queries on Job Event Data ####

Tower users will be able to run queries against Job Event Data.
The set of data targeted includes detailed event data, such as plays, tasks and changes made.

Event Data information to be retrieved includes the following fields:

* Status: status of the job Running, Pending, Successful, or Failed and its start time.
* Template for this job
* Job Type of Run, Check, or Scan
* Launched by username associated with this job
* Inventory associated with this job
* Project associated with this job
* Playbook that is being run
* Credential in use
* Verbosity setting for this job
* Extra Variables that this job used
* Plays start time
* Plays elapsed time
* Plays Name
* Plays result: whether the play succeeded or failed
* Task Success: the playbook task returned.
* Task Changed: the playbook task actually executed. Since Ansible tasks should be written to be idempotent, tasks may exit successfully without executing anything on the host. In these cases, the task would return Ok, but not Changed.
* Task Failure: the task failed. Further playbook execution was stopped for this host.
* Task Unreachable: the host was unreachable from the network or had another fatal error associated with it.
* Task Skipped: the playbook task was skipped because no change was necessary for the host to reach the target state.
* Host Event Host: for selected play and task
* Host Event Status
* Host Event unique ID
* Host Event Created On time stamp
* Host Event Role for this task
* Host Event name of the Play
* Host Event name of the Task
* Host Event Ansible Module for the task, and any arguments for that module
