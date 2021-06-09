---
layout: post
title: AWS EKS 쿠버네티스에서 JupyterHub 설치하기
date: 2021-05-28 00:00:00 +0900
author: 전지호
tags: docker kubernetes jupyter aws
excerpt: 쿠버네티스에 여러명의 분석가가 함께 작업할 수 있는 JupyterHub를 구축해보십니다. 각자 분리된 환경에서 일할 수 있으면 참 좋겠죠?
use_math: false
toc: true
# tags: 자동 수집되는 태그 띄어쓰기로 구분, 반드시 소문자로 사용
# excerpt: 메인 화면에 노출되는 post의 description
# use_math : 수식이 필요 할 경우(윗 첨자, 아랫첨자 동시 사용 불가) true | false
# toc : 목차가 필요 할 경우 true | false
# emoji 사이트: https://getemoji.com/
---


# 쿠버네티스에 JupyterHub 설치 👨‍💻

> 쿠버네티스가 구축되어 있다면, helm 차트를 이용하여 간단하게 JupyterHub를 설치할 수 있습니다.

<br/>

일단 작업환경을 수행할 폴더를 만들고 해당 폴더안에서 작업을 수행합니다.

해당 폴더는 JupyterHub의 앞으로의 configration을 담당할 폴더입니다.

<br/>

## 첫 번째, helm repogitory 업데이트

<hr/>

쿠버네티스 환경에 연결되어 있고, helm이 설치되어 있다면 다음의 명령어로 차트를 설치할 수 있습니다.

```shell
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
```
<br/>

다음과 같은 출력이 보여야합니다.

```shell
Hang tight while we grab the latest from your chart repositories...
...Skip local chart repository
...Successfully got an update from the "stable" chart repository
...Successfully got an update from the "jupyterhub" chart repository
Update Complete. ⎈ Happy Helming!⎈
```

<br/>

## 두 번째, JupyterHub 차트 다운로드

<hr/>

차트를 바로 설치하기 보단 템플릿의 구성을 확인하고 설치하기 위해 차트를 다운로드합니다.

```shell
helm fetch jupyterhub/jupyterhub
```
다운로드가 완료되면 압축된 차트 파일이 보입니다. 압축을 해제합니다.

```shell
tar -zxvf .\<다운로드된파일>.tgz
```
<br/>

![주피터허브 폴더구조](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/jhubdir.JPG){: #popup }

<br/>

## 세 번째, 템플릿을 변경할 수 있는 구성 파일을 만들어 봅시다.

<hr/>

helm 차트 리소스에 기본적으로 설치할 구성요소에 대한 리소스가 모두 포함되어 있습니다.

하지만 config.yaml 파일을 이용하면 구성요서에 대한 템플릿의 변경이 가능합니다.

그렇기때문에, config.yaml을 만들어 참조하고 설정을 변경해봅시다.

아래와 같이 빈 config.yaml을 만들어 작업 폴더 밑 차트 폴더에에 추가해주세요.(Chart.yaml과 같은 위치)


```yaml
# This file can update the JupyterHub Helm chart's default configuration values.
#
# For reference see the configuration reference and default values, but make
# sure to refer to the Helm chart version of interest to you!
#
# Introduction to YAML:     https://www.youtube.com/watch?v=cdLNKUoMc6c
# Chart config reference:   https://zero-to-jupyterhub.readthedocs.io/en/stable/resources/reference.html
# Chart default values:     https://github.com/jupyterhub/zero-to-jupyterhub-k8s/blob/HEAD/jupyterhub/values.yaml
# Available chart versions: https://jupyterhub.github.io/helm-chart/
#
```
<br/>

## 네 번째, 차트를 쿠버네티스 환경에 배포하여 설치해봅시다.

<hr/>

차트 폴더에서 아래의 명령어를 입력해주세요.

```shell
helm upgrade --cleanup-on-fail --install jhub . --namespace jhub --create-namespace --values config.yaml
```

🤬🤬🤬


아래와 같은 에러가 있다면, 배포환경에 토큰이 꼭 필요하단 이야기입니다.(예시: AWS EKS)

![토큰필요](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/tokenerror.JPG){: #popup }

<br/>

Openssl이나 여타 다른 토큰 제네레이터 프로그램을 이용하여 32자리의 hex코드를 임의로 생성해주세요.

폴더 안 values.yaml 파일에 시크릿 토큰을 입력하는 곳이 있습니다.

![토큰넣기](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/requiredtokken.JPG){: #popup }

<br/>

시크릿 토큰 입력

![토큰성공](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/requiredtokkensuccess.JPG){: #popup }

<br/>

다시 명령어를 입력해주세요.

```shell
helm upgrade --cleanup-on-fail --install jhub . --namespace jhub --create-namespace --values config.yaml
```
인스톨이 성공했습니다.

![주피터허브인스톨](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/installsuccess.JPG){: #popup }

Pod가 모두 잘 돌아갑니다.

```shell
kubectl get pod -n jhub
```

![주피터허브파드](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/pods.JPG){: #popup }

<br/>

외부접속을 위한 서비스도 볼 수 있습니다.

```shell
kubectl get svc -n jhub
```

![주피터허브서비스](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/svc.JPG){: #popup }

<br/>

## 다섯 번째, JupyterHub 접속하기

<hr/>

서비스에 나온 퍼블릭 주소로 접근해봅시다.

![외부접속](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/connectsuccess.JPG){: #popup }

쿠버네티스에 설치된 주피터 허브에 접속이 가능합니다!!(로드밸런서 설정은 따로 해주세요.)

아무 아이디로 로그인을 해봅시다.

<br/>

로그인 후에 사용자별 서버가 생성되는 것을 알 수 있습니다.

![서버생성](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/servercreate.JPG){: #popup }

<br/>

주피터 노트북이 떳습니다!

![주피터허브](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/jupyterhub.JPG){: #popup }

<br/>

다음 명령어를 입력해보면,

```shell
kubectl get pod -n jhub
```

![유저별파드](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/userpod.JPG){: #popup }

유저별로 Pod가 생성된 유연한 환경 분리가 가능한 것을 알 수 있습니다.

<br/>

## 마지막, JupyterHub 삭제

<hr/>

JupyterHub를 삭제하려면 간단하게 다음 명령어를 입력하면 됩니다.

```shell
helm uninstall jhub -n jhub
```

<br/>

## 가능한 것들

<hr/>

JupyterHub를 쿠버네티스 환경에 구축하므로서 생각했던 두 가지 목표가 가능해졌습니다. 

+ 사용자 별 다른 주피터 노트북 환경 구성 (pyspark-notebook, datascience-notebook)
+ 사용자 별 GPU 점유 주피터 노트북 (pyspark-notebook, datascience-notebook)

다음 포스트에서는 config.yaml을 수정하여 위와 같은 활동을 다뤄보겠습니다.

🖐🖐🖐

<br/>

## 참고문헌
👉 [zero-to-jupyterhub](https://zero-to-jupyterhub.readthedocs.io/en/latest/jupyterhub/installation.html#install-jupyterhub)


👉 [zero-to-jupyterhub-on-k8s](https://zero-to-jupyterhub.readthedocs.io/en/latest/kubernetes/setup-kubernetes.html)