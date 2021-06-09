---
layout: post
title:  Apache Zeppelin과 Jupyter의 비교
date:   2021-06-04 00:00:00 +0900
author: 전지호
tags: zeppelin jupyter
excerpt: 데이터 분석의 워크플로를 개선하는 아파치 제플린과 주피터를 간단하게 비교해볼께요.
use_math: false
toc: true
# tags: 자동 수집되는 태그 띄어쓰기로 구분, 반드시 소문자로 사용
# excerpt: 메인 화면에 노출되는 post의 description
# use_math : 수식이 필요 할 경우(윗 첨자, 아랫첨자 동시 사용 불가) true | false
# toc : 목차가 필요 할 경우 true | false
# emoji 사이트: https://getemoji.com/
---


# 아피치 제플린과 주피터의 간단 비교

<br/>

> 데이터 분석의 워크플로를 개선하는 아파치 제플린과 주피터를 간단하게 비교해볼께요.

<br/>

## 1. 설치 🛠

<hr/>

> 설치 단계에서부터 막히면, 아주 짜증이 많이납니다.

주피터의 설치는 아주 간단합니다. 

그냥 명령어를 통해 로컬에 설치만 하면 됩니다.

로컬 환경을 쉽게 서버에 올리기 위해, 버전 별로 빌드된 도커 버전도 제공합니다.

![다양한 주피터 도커](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/%EC%A3%BC%ED%94%BC%ED%84%B0%20%EC%84%A0%ED%83%9D.JPG){: #popup }

👉 [주피터](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html)


👉 [주피터 도커 깃허브](https://github.com/jupyter/docker-stacks)

그에 비해, 제플린의 설치는 조금 더 복잡합니다. 압축을 풀고 서버에서 실행해야 하죠.

많은 기능을 함께 사용할려면 소스를 빌드하고 다시 실행해하는 문제가 있습니다.

<b><u>첫 번째 대결은, Jupyter의 손을 들어줍니다.</u></b>

<br/>

## 2. 커뮤니티 💬

<hr/>

> 큰 커뮤니티는 레퍼런스와 도움을 받기 위해 아주 중요한 요소입니다.

Jupyter의 커뮤니티는 이 Zeppelin보다 상당히 크고 훨씬 더 많은 외부 시스템을 지원합니다. 

그러나 Zeppelin의 커뮤니티는 성장 중이나 아직은 Jupyter에 밀리는 모습을 보여줍니다.

<b><u>두 번째 대결은, Jupyter의 손을 들어줍니다.</u></b>

![구글 트렌드 비교](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/compatition.jpg){: #popup }

<br/>

## 3. 다중 사용자 지원 👨‍👩‍👦‍👦

<hr/>

> 공용 환경에서 다중 사용자 지원은 필수입니다.

Zeppelin는 다중 사용자를 지원하며,  Jupyter는 다중 사용자를 지원하지 않습니다.

세 번째 대결은, Zeppelin의 승리일까요?

JupyterHub라는 Jupyter 확장 리소스는 다중 사용자 지원을 약속합니다.

하지만 Zeppelin에 비해 Jupyter는 사용자마다 별도의 서버가 필요합니다.

<b><u>이어질 내용으로 인해 이번 대결은 보류하겠습니다.</u></b>

<br/>

## 4. 다중 사용자 지원 시 리소스 분배 👨‍👩‍👦‍👦

<hr/>

> 다중 사용자가 많은 리소스를 동시에 사용할 때, 이에 대한 대응은 어떨까요?

Zeppelin은 서버 단일 프로세스를 사용합니다. 다중 사용자의 이용에 취약하죠.

이를 회피하기 위해, conda 환경과 docker를 Zeppelin 내부에서 지원합니다.

Jupyter는 어떨까요?

Jupyter는 애초에 다중 사용자를 지원하지않으니, JupyterHub를 살펴봅시다.

JupyterHub는 각 사용자마다 서버를 따로 제공해야하니 단일 서버 프로세스를 사용한다 하더라도, 서로 영향을 주지 않습니다.

하지만 각각의 서버를 구축하는 비용에 대한 문제는 어떻게 할까요?

JupyterHub는 쿠버네티스 환경을 제공하는 버전을 따로 내놨습니다.

하나의 서버에서 동작하는 쿠버네티스 환경에서의 JupyterHub는 각각의 사용자에 대해 가상의 컨테이너를 제공하여, 분리된 작업환경을 제공하는 동시에 서버 구축 비용을 줄일 수 있습니다.

<b><u>네 번째 대결은, 주피터의 손을 들어줍니다.</u></b>

<br/>

## 5. 확장프로그램 📥

<hr/>

> 더 많은 기능을 사용하고 싶다면...

Jupyter는 약 20 개만있는 Zeppelin의 인터프리터 유형에 대해 지원되는 엔진이 85 개가 넘는 큰 목록으로 인해 승리합니다. 다양한 언어를 사용하고 싶다면, 주피터를 사용해야 합니다.

<br/>

## 6. 차트 📊 📈 📉

<hr/>

> 데이터 시각화를 이용하여, 비주얼라이징 툴을 사용할 수 있습니다.

Jupyter와 Zeppelin을 둘 다 다양한 비주얼라이징 툴을 플로팅하여 사용할 수 있습니다.

<b><u>따라서, 대결은 무승부입니다.</u></b>

<br/>

## 7. 결론

<hr/>

> 개인의 선호도에 따라, 선택은 자유.

하지만, 많은 부분에서 Jupyter의 우세를 점칠 수 있습니다. 최근 가장 핫한 개발트렌드인 docker와 쿠버네티스 지원이 우수한 것은 차이를 더 크게 만드는 요소일 수도 있습니다.

위와 같은 이유로,

우리 팀은 <b><u>쿠버네티스 환경에 JupyterHub</u></b>를 구축하여 사용하고 있습니다.

도움이 되셨길 바랍니다.

![넷플릭스도 쓰는 주피터](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/netflixjupyter.png){: #popup }

<br/>

안녕👋