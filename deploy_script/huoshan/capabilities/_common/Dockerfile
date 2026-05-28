ARG CAPABILITY_BASE_IMAGE
FROM ${CAPABILITY_BASE_IMAGE}

ARG CAPABILITY_RUN_SCRIPT

COPY zou /opt/application/zou
COPY ${CAPABILITY_RUN_SCRIPT} /opt/application/run.sh

RUN chmod +x /opt/application/run.sh

EXPOSE 8000

CMD /opt/application/run.sh
