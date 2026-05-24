source ~/.bash_profile
docker login ccr.ccs.tencentyun.com --username=100036567968 --password=DCC2024cloud
docker build -t ccr.ccs.tencentyun.com/dcc-cloud/asr_provider:0.0.1 -f ../../fc_src/Dockerfile ../../fc_src
docker push ccr.ccs.tencentyun.com/dcc-cloud/asr_provider:0.0.1
scf deploy