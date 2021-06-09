---
layout: post
title:  Jupyter Notebook 도커 GPU 연동하기(tensorflow, pytorch, gpu-jupyter)
date:   2021-06-09 00:00:00 +0900
author: 배터리호
tags: jupyter docker tensorflow pytorch
excerpt: 도커로 만든 도커라이즈 Jupyter Notebook의 유용함을 느끼다보면, 자연스럽게 tensorflow 같은 딥러닝 프레임워크가 설치된 Jupyter Notebook도 사용할 수 있게 됩니다. 하지만 GPU 가속을 사용하기 위해선 한가지 장애물을 또 넘어야 합니다. gpu-jupyter 프로젝트가 도와줄 것입니다.
use_math: false
toc: true
# tags: 자동 수집되는 태그 띄어쓰기로 구분, 반드시 소문자로 사용
# excerpt: 메인 화면에 노출되는 post의 description
# use_math : 수식이 필요 할 경우(윗 첨자, 아랫첨자 동시 사용 불가) true | false
# toc : 목차가 필요 할 경우 true | false
---


# 도커라이즈 Jupyter Notebook에 GPU 가속 더하기

> GPU 가속도 사용할 수 있으면서, pytorch, tensorflow등 딥러닝 프레임워크가 설치된 jupyter notebook이 있습니다.

<br/>

## 개요

<hr/>

👉 [<u>주피터 도커 프로젝트</u>](https://jupyter-docker-stacks.readthedocs.io/en/latest/index.html)

jupyter notebook을 도커라이즈하는 프로젝트는 이미 궤도에 올라섰습니다. 아주 편하게 사용할 수 있죠.

공식 주피터 도커 Document에서 선택할 수 있는 이미지 중 딥러닝 프레임워크를 다룰 수 있는 이미지는 다음과 같습니다.

- jupyter/tensorflow-notebook
- jupyter/datascience-notebook

<u><b>공식 jupyter docker Document에 pytorch, keras를 공식적으로 제공하지 않습니다.</b></u>

또한, 위 두가지 도커 이미지도 GPU를 지원하지 않습니다.

만약, jupyter notebook에 pytorch와 GPU 가속을 사용하고 싶다면, 어떻게 해야할까요?

물론, 도커 이미지를 직접 만들면 되겠지만, 도커 이미지에 직접 딥러닝 프레임워크를 설치하는 것은 사실 쉬운 문제가 아닙니다.

> 그러나, GPU 가속도 사용할 수 있으면서, pytorch, tensorflow등 딥러닝 프레임워크가 설치된 jupyter notebook이 있습니다

공식 jupyter docker Document에 community stacks에 있는 이 프로젝트의 이미지를 잘 사용하면,

jupyter notebook에서 딥러닝 프레임워크와 함께 GPU 가속을 사용할 수 있습니다.

<br/>

## GPU-jupyter

<hr/>

해당 프로젝트의 Github의 주소는 다음과 같습니다.

👉 [<u>GPU-jupyter</u>](https://github.com/iot-salzburg/gpu-jupyter/)

GPU-jupyter에 이미지를 pull하면 최신 버전의 pytorch, tensorflow가 설치된 jupyter notebook을 사용할 수 있습니다.

Github를 조금만 살펴보면 cuda, cudnn의 버전을 선택해서 사용할 수 있는 것을 알 수 있습니다.

2021년 6월 9일 자, 사용 가능한 cuda, cudnn의 버전을 명시한 이미지는 다음과 같습니다.

- v1.4_cuda-11.0_ubuntu-20.04 (full image)
- v1.4_cuda-11.0_ubuntu-20.04_python-only (only with a python interpreter and without Julia and R)
- v1.4_cuda-11.0_ubuntu-20.04_slim (only with a python interpreter and without additional packages)
- v1.4_cuda-11.0_ubuntu-18.04 (full image)
- v1.4_cuda-11.0_ubuntu-18.04_python-only (only with a python interpreter and without Julia and R)
- v1.4_cuda-11.0_ubuntu-18.04_slim (only with a python interpreter and without additional packages)
- v1.4_cuda-10.1_ubuntu-18.04 (full image)
- v1.4_cuda-10.1_ubuntu-18.04_python-only (only with a python interpreter and without Julia and R)
- v1.4_cuda-10.1_ubuntu-18.04_slim (only with a python interpreter and without additional packages)

<br/>

## 커스터마이징 하기 위해 GPU-jupyter 구조 살펴보기

<hr/>

> GPU-jupyter는 어떤 구조로 jupyter notebook에 딥러닝 프레임워크를 설치했는지 살펴보는 것은 중요합니다.

딥러닝 프로젝트는 프레임워크에 대한 의존성이 매우 심하기 때문에, 개발자가 원하는 프레임워크를 지정해서 설치하고 사용하는 경우가 많습니다.

GPU-jupyter 프로젝트는 완벽하진 않지만 프레임워크를 지정하여 설치하고 사용할 수 있도록 커스터마이징을 할 수 있게 도와줍니다.

일단 해당 프로젝트를 clone 받아봅시다.

``` shell
git clone https://github.com/iot-salzburg/gpu-jupyter.git
```


<br/>
