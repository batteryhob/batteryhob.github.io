---
layout: post
title: AWS EKS 쿠버네티스에서 JupyterHub 환경 설정하기
date: 2021-05-31 00:00:00 +0900
author: 전지호
tags: docker kubernetes jupyter aws
excerpt: JupyterHub를 구축했다면 사용자 별 환경과 리소스를 구분하기 위한 설정방법을 알아봅시다.
use_math: false
toc: true
# tags: 자동 수집되는 태그 띄어쓰기로 구분, 반드시 소문자로 사용
# excerpt: 메인 화면에 노출되는 post의 description
# use_math : 수식이 필요 할 경우(윗 첨자, 아랫첨자 동시 사용 불가) true | false
# toc : 목차가 필요 할 경우 true | false
# emoji 사이트: https://getemoji.com/
---


# 쿠버네티스 JupyterHub 설정법 👨‍💻

> config.yaml을 이용한 사용자 별 환경 구성법

<br/>

## 첫 번째, config.yaml이 작업 폴더에 있는지 확인해 주세요.

<hr/>

👉 [첫번째 포스트](/2021/05/27/JupyterhubForK8S-전지호.html)

위 포스트 처음에 만들었던 config.yaml를 확인합니다.

![config.yaml 위치](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/config%EC%9C%84%EC%B9%98.JPG){: #popup }

config.yaml을 수정하고 다음 명령어를 입력하면 변경사항이 jupyterhub에 적용됩니다.

``` shell
helm upgrade --cleanup-on-fail --install jhub . --namespace jhub --values config.yaml
```

<br/>

## 두 번째, 기본으로 사용되는 jupyter 이미지를 사양에 맡게 변경해봅시다.

<hr/>

다음과 같이 config.yaml을 수정하면 기본 도커이미지가 jupyter/datascience-notebook로 변경됩니다.

사무실 환경에 맡게 커스텀한 도커이미지를 도커허브에 푸쉬한 뒤 그것을 사용해도 무방합니다.

``` yaml
singleuser:
  image:
    # You should replace the "latest" tag with a fixed version from:
    # https://hub.docker.com/r/jupyter/datascience-notebook/tags/
    # Inspect the Dockerfile at:
    # https://github.com/jupyter/docker-stacks/tree/HEAD/datascience-notebook/Dockerfile
    name: jupyter/datascience-notebook
    tag: latest
```
<br/>

## 세 번째, jupyterlab을 기본으로 사용해봅시다.

<hr/>

``` yaml
singleuser:
  defaultUrl: "/lab"
```

![주피터랩](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/%EC%A3%BC%ED%94%BC%ED%84%B0%EB%9E%A9.JPG){: #popup }

<br/>

## 네 번째, 다양한 주피터 이미지를 선택할 수 있게 합시다.

<hr/>

profileList에 항목을 추가하면 로그인 시 이미지를 선택하여 jupyter를 실행할 수 있습니다.

아래 예는 pyspark버전과 datascience버전을 선택할 수 있는 예제입니다.

선택하지 않으면, jupyter/minimal-notebook이 실행됩니다.

``` yaml
singleuser:
  defaultUrl: "/lab"
  image:
    name: jupyter/minimal-notebook
    tag: latest
  profileList:
    - display_name: "MLP Jupyter Notebook | pyspark"
      description: "spark를 사용할 수 있는 일반 jupyter notebook"
      kubespawner_override:
        image: jupyter/pyspark-notebook
        tag: latest
    - display_name: "MLP Jupyter Notebook  | tensorflow"
      description: "tensorflow가 설치되어 있는 jupyter notebook"
      kubespawner_override:
        image: jupyter/tensorflow-notebook
        tag: 7a0c7325e470
```

![원하는 주피터로 시작](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/%EC%A3%BC%ED%94%BC%ED%84%B0%EC%9D%B4%EB%AF%B8%EC%A7%80%EC%84%A0%ED%83%9D.JPG){: #popup }

<br/>

## 다섯 번째, 사용자와 비밀번호를 설정하는 방법

<hr/>

아래와 같이 입력하면 2명의 관리자 유저, 2명의 일반 유저, 공통 비밀번호로 접근할 수 있습니다.

``` yaml
hub:
  config:
    Authenticator:
      admin_users:
        - admin
        - batteryho
      allowed_users:
        - seungjin
        - ehdud8565
        - yeonsuuu
        - sanghyunbaek
        - hgchoi16
    DummyAuthenticator:
      password: <비밀번호입력>
    JupyterHub:
      authenticator_class: dummy
singleuser:
# 생략
```

<br/>

## 리소스를 설정하는 방법

<hr/>

쿠버네티스내에 jupyter notebook들은 기본적으로 각 사용자에게는 1G의 RAM 이 보장 됩니다. 모든 사용자는 1G 이상을 가지고 있지만 가능한 경우 기술적으로 더 많이 사용할 수 있습니다. 

다음과 같이 입력하여 메모리 제한을 변경할 수 있습니다.

guarantee는 필요에 의해 남아있는 다른 리소스를 사용하는 것을 의미하고,

limit는 더이상 리소스를 사용하지 못함을 의미 합니다.

``` yaml
singleuser:
  memory:
    limit: 2G
    guarantee: 1G
```

cpu의 제한 또한 다음과 같이 변경할 수 있습니다.

``` yaml
singleuser:
  cpu:
    limit: .5
    guarantee: .5
```
<br/>

## GPU 할당하는 방법

<hr/>

tensorflow나 pytorch같은 딥러닝 프레임워크들은 GPU를 사용할 수 있습니다.

다음과 같이 입력하여 gpu 할당이 가능합니다.

물론, 쿠버네티스 환경에 gpu가 있어야합니다.

``` yaml
singleuser:
  defaultUrl: "/lab"
  image:
    name: jupyter/minimal-notebook
    tag: latest
  profileList:
    - display_name: "MLP Jupyter Notebook | pyspark"
      description: "spark를 사용할 수 있는 일반 jupyter notebook"
      kubespawner_override:
        image: jupyter/pyspark-notebook
        tag: latest
    - display_name: "MLP Jupyter Notebook  | tensorflow"
      description: "tensorflow가 설치되어 있는 jupyter notebook"
      kubespawner_override:
        image: jupyter/tensorflow-notebook
        tag: 7a0c7325e470
        # 해당부분
        extra_resource_limits:
          nvidia.com/gpu: "1"
```

기본적인 사용방법을 알아봤습니다.

더 많은 정보는 아래 링크에서 확인해주세요.

<br/>

## 참고문헌

👉 [zero-to-jupyterhub-on-k8s](https://zero-to-jupyterhub.readthedocs.io/en/latest/kubernetes/setup-kubernetes.html)