---
layout: default
title: Orchestrate scans
parent: Documentation
nav_order: 9
---

# Orchestrate scans

This section explains how to run scans as part of your data pipeline and
stop the pipeline when necessary to prevent bad data flowing downstream.

Soda SQL is build in such a way that it's easy to run it as a step in your
pipeline orchestration.

Use your orchestration tool to configure if the soda scan should be blocking the pipeline
(for testing) or run in parallel (for monitoring).

## Airflow

There are several options to run Soda SQL with Airflow. You can use the
BashOperator to invoke soda scan which is installed in same environment as
Airflow, or in a different virtual environment, or you can use PythonOperator to
trigger soda scans.

### Using BashOperator

The simplest way is to install Soda SQL in the same environment
as your Airflow and invoke `soda scan` using Airflow BashOperator.

When there are test failures in soda scan, the exit code will be non-zero.

To create a BashOperator, first create a variable in airflow to point to your
Soda SQL project. You can do this either using Airflow web admin ui or via
commandline:

```bash
airflow variables set "soda_sql_project_path" "YOUR_SODA_SQL_PROJECT_LOCATION"
```

Take a note of the variable name and use it in your DAG. Here is a sample DAG
that uses Airflow DummyOperators to denote data ingestion task and publishing
task:

```python
from airflow import DAG
from airflow.models.variable import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

# Use the same variable name that you used in airflow variable creation
soda_sql_project_path = Variable.get('soda_sql_project_path')

default_args = {
    'owner': 'soda_sql',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'soda_sql_scan',
    default_args=default_args,
    description='A simple Soda SQL scan DAG',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
)
# A dummy operator to simulate data ingestion
ingest_data_op = DummyOperator(
    task_id='ingest_data'
)

# Soda SQL Scan which will run the appropriate table scan for the ingestion
soda_sql_scan_op = BashOperator(
    task_id='soda_sql_scan_demodata',
    bash_command=f'cd {soda_sql_project_path} && soda scan warehouse.yml tables/demodata.yml',
    dag=dag
)

# A dummy operator to simulate data publication when the Soda SQL Scan task is successful
publish_data_op = DummyOperator(
    task_id='publish_data'
)

ingest_data_op >> soda_sql_scan_op >> publish_data_op

```

In the above DAG, `soda_sql_scan_demodata` task will fail when the tests you
defined for `demodata` table fails. This will prevent the `publish_data_op` from
running. You can further customize the bash command to use different soda scan command
options, for example passing variables to `soda scan` command.

### Using soda from virtualenv

If for some reason, you can't install Soda SQL in the same python environment as
Airflow, you can use a separate virtualenv for Soda SQL.

Using your favorite virtualenv management tool create a venv, we will use
`virtualenv` command as example. Please review soda-sql installation
requirements to use tested python version for creating the virtualenv.

```shell
# create a new virtualenv in a convenient location
virtualenv .sodavenv
# install soda-sql using pip
.sodavenv/bin/pip install soda-sql
# test if soda command works as expected
❯ .sodavenv/bin/soda --help
Usage: soda [OPTIONS] COMMAND [ARGS]...

  Soda CLI version 2.0.0b10

Options:
  --help  Show this message and exit.

Commands:
  create  Creates a new warehouse.yml file and prepares credentials in your...
  init    Finds tables in the warehouse and creates scan YAML files based
          on...

  scan    Computes all measurements and runs all tests on one table.
```

Now you can modify the BashOperator in the above DAG as follows:

```python
soda_sql_scan_op = BashOperator(
    task_id='soda_sql_scan_demodata',
    bash_command=f'cd {soda_sql_project_path} && .sodavenv/bin/soda scan warehouse.yml tables/demodata.yml',
    dag=dag
)
```

### Using PythonOperator

If you installed Soda SQL in your python environment you can also use
PythonOperator to invoke Soda Scan. The following shows a sample Airflow DAG
using PythonOperator that you can use as a starting point.

```python
from airflow import DAG
from airflow.models.variable import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
from sodasql.scan.scan_builder import ScanBuilder
from airflow.exceptions import AirflowFailException

# Make sure that this variables are set in your Airflow
warehouse_yml = Variable.get('soda_sql_warehouse_yml_path')
scan_yml = Variable.get('soda_sql_scan_yml_path')

default_args = {
    'owner': 'soda_sql',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def run_soda_scan(warehouse_yml_file, scan_yml_file):
    scan_builder = ScanBuilder()
    scan_builder.warehouse_yml_file = warehouse_yml_file
    scan_builder.scan_yml_file = scan_yml_file
    scan = scan_builder.build()
    scan_result = scan.execute()
    if scan_result.has_failures():
        failures = scan_result.failures_count()
        raise AirflowFailException(f"Soda Scan found {failures} errors in your data!")


dag = DAG(
    'soda_sql_python_op',
    default_args=default_args,
    description='A simple Soda SQL scan DAG',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
)

ingest_data_op = DummyOperator(
    task_id='ingest_data'
)

soda_sql_scan_op = PythonOperator(
    task_id='soda_sql_scan_demodata',
    python_callable=run_soda_scan,
    op_kwargs={'warehouse_yml_file': warehouse_yml,
               'scan_yml_file': scan_yml},
    dag=dag
)

publish_data_op = DummyOperator(
    task_id='publish_data'
)

ingest_data_op >> soda_sql_scan_op >> publish_data_op

```
###  Using PythonVirtualenvOperator

If you can't install soda-sql to your Ariflow environemnt, you can use
PythonVirtualenvOperator to run Soda scan in a different environment. Please
make sure that you have `virtualenv` installed in your main Airflow environment.


```python
from airflow import DAG
from airflow.models.variable import Variable
from airflow.operators.python import PythonVirtualenvOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from datetime import timedelta



# Make sure that this variable is set in your Airflow
warehouse_yml = Variable.get('soda_sql_warehouse_yml_path')
scan_yml = Variable.get('soda_sql_scan_yml_path')

default_args = {
    'owner': 'soda_sql',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def run_soda_scan(warehouse_yml_file, scan_yml_file):
    from sodasql.scan.scan_builder import ScanBuilder
    scan_builder = ScanBuilder()
    # Optionally you can directly build the Warehouse dict from Airflow secrets/variables
    # and set scan_builder.warehouse_dict with values.
    scan_builder.warehouse_yml_file = warehouse_yml_file
    scan_builder.scan_yml_file = scan_yml_file
    scan = scan_builder.build()
    scan_result = scan.execute()
    if scan_result.has_failures():
        failures = scan_result.failures_count()
        raise ValueError(f"Soda Scan found {failures} errors in your data!")


dag = DAG(
    'soda_sql_python_venv_op',
    default_args=default_args,
    description='A simple Soda SQL scan DAG',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
)

ingest_data_op = DummyOperator(
    task_id='ingest_data'
)

soda_sql_scan_op = PythonVirtualenvOperator(
    task_id='soda_sql_scan_demodata',
    python_callable=run_soda_scan,
    requirements=["soda-sql==2.0.0b10"],
    system_site_packages=False,
    op_kwargs={'warehouse_yml_file': warehouse_yml,
               'scan_yml_file': scan_yml},
    dag=dag
)

publish_data_op = DummyOperator(
    task_id='publish_data'
)

ingest_data_op >> soda_sql_scan_op >> publish_data_op

```

### SodaScanOperator -- Coming Soon!

We are currently working on a custom Soda SQL operator to provide even tighter
integration with Airflow.

Need more help? [Post your questions on GitHub](https://github.com/sodadata/soda-sql/discussions)
or [join our Slack community](https://join.slack.com/t/soda-community/shared_invite/zt-m77gajo1-nXJF7JtbbRht2zwaiLb9pg)

## Other orchestration solutions

If you're reading this and thinking: "I want to contribute!" Great.
[Post an note on GitHub](https://github.com/sodadata/soda-sql/discussions) to let
others know you're starting on this.

TODO: describe how to run Soda scans in orchestration tools like

* AWS Glue

* Dagster
* Fivetran
* Matillion
* Luigi

If you're reading this and thinking: "I want to contribute!" Great.
[Post an note on GitHub](https://github.com/sodadata/soda-sql/discussions) to let others know
you're starting on this.
