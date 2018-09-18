FROM cfmeqe/sel_ff_chrome_new

ENV PROJECT integration_tests

ADD . cfme_tests

RUN dnf install -y git python-pip gcc postgresql-devel libxml2-devel libxslt-devel tigervnc-server fluxbox xterm java-1.8.0-openjdk.x86_64 \
libcurl-devel python-devel redhat-rpm-config libffi-devel openssl-devel python-setuptools sshpass \
findutils tmux && dnf clean all

RUN pip install -U pip && pip install -U virtualenv

WORKDIR cfme_tests

RUN virtualenv cfme_venv

RUN . cfme_venv/bin/activate

RUN export PYCURL_SSL_LIBRARY=openssl

#RUN pip install -r $PROJECT/requirements/frozen.txt

WORKDIR $PROJECT/

RUN python -m cfme.scripting.quickstart

USER 0
# runtime
EXPOSE 22
EXPOSE 4444
EXPOSE 5999
ENTRYPOINT ["/bin/bash", "/xstartup.sh"]
