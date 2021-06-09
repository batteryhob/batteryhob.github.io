---
layout: post
title:  AWS S3 데이터 Lifecycle 기능을 이용하여 정리하기
date:   2021-06-04 00:00:00 +0900
author: 전지호
tags: aws
excerpt: S3를 이용하여 로그 및 분석 결과 혹은 파일을 저장하여 사용하다 보면 어느새 너무 많은 양의 데이터가 축적됩니다. 이 중 사용하는 데이터나 파일은 상관이 없으나, 사용하지 않는 데이터가 너무 많이 쌓이면 문제가 발생할 수 도 있습니다. AWS Concsole이나 S3 Browser를 통해 이를 삭제하고 관리할 수 잇는 방법을 알아봅시다.
toc: false
use_math: false
# tags: 자동 수집되는 태그 띄어쓰기로 구분, 반드시 소문자로 사용
# excerpt: 메인 화면에 노출되는 post의 description
# toc : 목차가 필요 할 경우 true | false
# use_math : 수식이 필요 할 경우(윗 첨자, 아랫첨자 동시 사용 불가) true | false
# emoji 사이트: https://getemoji.com/
---

# "너는 어쩜 정리도 안하고 방을 돼지우리 같이 하고 사니..."

> 우리, S3라도 정리합시다. 꿀꿀 🐷

<br/>

Amazon S3를 이용하여 로그 및 분석 결과 혹은 파일을 저장하여 사용하다 보면 어느새 너무 많은 양의 데이터가 축적됩니다.

데이터가 많아지면 많아질 수록, 스토리지 요금도 엄청나게 발생하게 됩니다.

![엄청난 용량](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/s3lifecycle/%EC%97%84%EC%B2%AD%EB%82%9C%EC%9A%A9%EB%9F%89.JPG){: #popup }

이 중 사용하는 데이터나 파일은 상관이 없으나, 사용하지 않는 데이터가 너무 많이 쌓이면 문제가 발생할 수 도 있습니다. 

AWS Concsole이나 S3 Browser를 통해 데이터에 접근할 때, 많은 데이터 조회에 속도가 느려지는 현상도 목격할 수 있어요.

S3의 Lifecycle 기능을 이용하여 S3 버킷에 있는 데이터를 삭제하고 관리할 수 잇는 방법을 알아봅시다.

<br/>

## Amazon S3 Lifecycle 기능 사용하기

<hr/>

먼저, AWS Concsole로 S3 메뉴로 접근합니다. 

그리고 버킷 리스트 중 정리를 할 S3 버킷을 클릭해 접근해보면 <u><b>관리</b></u>라는 메뉴가 보여요.

![S3 버킷 접근](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/s3lifecycle/%EB%B2%84%ED%82%B7%EC%A0%91%EA%B7%BC.JPG){: #popup }

<u><b>수명 주기 규칙 생성</b></u>버튼을 눌러서 생성화면으로 접근합니다.

![수명주기 생성화면1](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/s3lifecycle/%EC%88%98%EB%AA%85%EC%A3%BC%EA%B8%B0%EC%83%9D%EC%84%B1%ED%99%94%EB%A9%B40.JPG){: #popup }

다음과 같은 화면을 볼 수 있어요.

![수명주기 생성화면2](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/s3lifecycle/%EC%88%98%EB%AA%85%EC%A3%BC%EA%B8%B0%EC%83%9D%EC%84%B1%ED%99%94%EB%A9%B41.JPG){: #popup }

수명 주기의 이름을 생성한 후, 범위를 지정해야 합니다. 

범위를 지정하지 않으면, 모든 객체가 해당 수명 주기의 영향을 받으니 주의해주시기 바랍니다.

보통은 파일명(접두사)로 구분합니다. 접두사를 입력해주시면, 해당 접두사에 포함된 항목만 수명 주기에 영향을 받습니다.

<br/>

### 접두사란?

S3에서 파일의 구조를 보면

<b><u>버킷이름/상위폴더명/하위폴더명/파일명</u></b> 

이렇게 된 폴더 구조를 볼 수 있는데, 이는 실제로는 폴더 구조가 아니라 폴더+파일명이 하나의 Key로 취급됩니다.

그렇기 때문에, 접두사는 파일명에 앞에 붙는 Key의 구분자라고 생각하시면 됩니다.

따라서, 바로 위의 경우는 버킷이름을 제외하고 슬래시를 포함하여(/) 

<b><u>상위폴더명/하위폴더명/</u></b>

까지가 해당 파일 Key의 접두사라고 보실 수 있습니다.

<br/>

## 수명 주기의 규칙

<hr/>

![수명주기 생성화면3](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/s3lifecycle/%EC%88%98%EB%AA%85%EC%A3%BC%EA%B8%B0%EC%83%9D%EC%84%B1%ED%99%94%EB%A9%B42.JPG){: #popup }

수명 주기의 규칙은 잘 쓰지 않는 마지막 조건을 제외하고, 4가지 조건을 볼 수 있습니다.

- 스토리지 클래스 간에 객체의 `현재`버전 반환
    - 해당 객체가 `최신` 버전으로 취급되는 시간입니다.
- 스토리지 클래스 간에 객체의 `이전`버전 반환
    - 해당 객체가 `이전` 버전으로 취급되는 시간입니다.
- 객체의 `현재` 버전 만료
    - 해당 객체가 `최신` 버전으로 취급되지 않을 때까지의 시간입니다.
- 객체의 `이전` 버전 영구 삭제
    - 해당 객체가 `이전` 버전으로 취급되어 영구적으로 삭제될 때까지의 시간입니다.

<br/>

저의 경우에는,

<b><u>S3에 업로드된 객체가 30일 후에 이전 버전으로 취급되고,</u></b>

<b><u>이전 버전이 된 지 60일이나 지나면 삭제하고 싶었습니다.</u></b>

결국, 총 90일 후 S3에 적재된 리소스를 삭제하고 싶었으므로,

2번과, 4번 조건을 이용해 수명 주기를 생성했습니다.

완료 버튼을 눌러 생성을 완료합니다.

![생성완료](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/s3lifecycle/%EC%83%9D%EC%84%B1%EC%99%84%EB%A3%8C.JPG){: #popup }

상세 화면을 보면 등록된 수명 주기를 확인할 수 있습니다.

![수명 주기 확인](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/s3lifecycle/%ED%83%80%EC%9E%84%EB%9D%BC%EC%9D%B8%ED%99%95%EC%9D%B8.JPG){: #popup }


<br/>

## 결론

<hr/>

> AWS S3 Lifecycle 기능을 사용하여 스토리지 요금을 줄이고, 복잡하지 않은 S3 파일 관리가 가능해졌습니다.

앞으로는 집에서 잔소리를 좀 듣더라도 데이터만이라도 잘 정리하여 

효과적인 업무를 할 수 있도록 노력합시다.

그럼 20,000👋
