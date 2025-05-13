# ansiblefest2025

## How does automation pay for itself?

Consumers of automation often feel the intrinsic value in their quality of life, quality of work, and efficiency. How do automation engineers convince the people in the corner office to invest? We take a look at some basic ways to measure automation and how to use those measurements to display a correlation between automation development and business value. We start with defining what is business value? We discuss ways to define metrics and to measure automation success including, but not limited to, Ansible Automation Analytics.

We will look at some basic measurement principles like engineer-hours saved and correlate that to money saved.
We will explain how to do some basic measurements such as ROI.

In the Automation Calculator directory there are some Jupyter notebooks that do some calculations and graphing in Python.

In the ansible-exporter directore, there is a python app that grabs data from Ansible Automation Platform and does some python calculations. It then exposes these metrics using FastAPI so that prometheus can ingest them and ultimately Grafana can display them.

Finally, in the playbooks directory there are some roles to build out a prometheus and grafana server. The Dashboard used in the lightning talk is available as a JSON file.
