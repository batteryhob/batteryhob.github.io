---
layout: post
title:  Nodejs에서 AWS DynamoDB를 조회하고 삭제하는 방법 알아보기 
date:   2021-06-29 00:00:00 +0900
author: 전지호
tags: nodejs dynamoDB
excerpt: Nodejs에서 AWS DynamoDB 데이터를 조회하는 방법을 알아봅시다. 해당 예제는 aws-sdk for Javasript를 사용합니다.
use_math: false
toc: true
---


# Nodejs에서 AWS DynamoDB를 사용할 수 있는 기본 조회/삭제 쿼리

> AWS DynamoDB 테이블에 대해 몇 가지 기본 쿼리를 실행합니다.

<br/>

## AWS-SDK for Javascript 설치

<hr/>

DynamoDB에 연결하기 위해서는, AWS-SDK를 설치해야 합니다.

AWS-SDK는 AWS요소를 사용하기 위해 필수적인 도구입니다.

npm이나 yarn을 사용해서 설치합니다.

``` shell
npm install aws-sdk
# or
yarn add aws-sdk
```
<br/>

## AWS-SDK for Javascript 설치 및 설정

<hr/>

설치가 완료되었으면, 인증을 위해 configration을 살펴봐야 합니다.

### 첫 번째, 본인의 accessKey 와 secrertAccessKey를 설정합니다.

이번 예제에서는 json을 사용하겠습니다.

임의의 공간에 aws.config.json이름의 json 파일을 생성합니다.

``` json
{ 
    "accessKeyId": "여기에 본인 것을 작성", 
    "secretAccessKey": "여기에 본인 것을 작성",
    "region": "ap-northeast-2" 
    // 서울로 지정했습니다.
}
```

사용하려는 곳에서 aws-sdk와 aws.config.json 불러와 설정해줍니다.

``` javascript
import AWS from "aws-sdk";

AWS.config.loadFromPath('./config/aws.config.json');
```

### 두 번째, 사용하려는 dynamoDB에 리전을 설정해줍니다.

본인 리전에 맞는 endpoint는 다음 링크에서 찾을 수 있습니다.

👉 [Amazon DynamoDB endpoints and quotas](https://docs.aws.amazon.com/general/latest/gr/ddb.html)

endpoint와 리전을 설정합니다.

``` javascript
import AWS from "aws-sdk";

AWS.config.loadFromPath('./config/aws.config.json');
//리전 설정
AWS.config.update({
    region: "ap-northeast-2",
    endpoint: "dynamodb.ap-northeast-2.amazonaws.com"
});
```

설정을 마무리했습니다.

이제 데이터를 조회해봅시다.

<br/>

##  DynamoDB 조회

<hr/>

### DynamoDB 단일 항목 Select

DynamoDB에 있는 단일 항목을 가져오기 위해, Key를 사용해야 합니다.

<u><b>예측가능한 프로그래밍을 위해 async, await구문을 사용하여, 순차 처리를 보장하는 것도 잊지 말아야합니다.</b></u>

``` javascript
export const selectData = async (_id) => {
    const params = {
        TableName: '테이블명',
        Key:{
            "id": _id
        }
    };

    try {
        const result = await docClient.get(params).promise();
        return result;
    }catch(e){
        console.log(e)
        return null
    }
}
```

### DynamoDB 조건 부 Select

일반적으로 생각하는 Select 구분의 기본적인 조회는 다음과 같은 구문을 사용합니다.

일반 RDB를 사용하는 것처럼 조회를 사용하려면 아래 구문으로 사용하면 조회할 수 있습니다.

KeyConditionExpression 사용하여, 조건에 해당하는 값을 명시해준 뒤,

ExpressionAttributeValues를 이용하여 값을 넣어줍시다.

<u><b>예측가능한 프로그래밍을 위해 async, await구문을 사용하여, 순차 처리를 보장하는 것도 잊지 말아야합니다.</b></u>

``` javascript
export const selectDatas = async (_id) => {
    const params = {
        TableName: '테이블명',
        KeyConditionExpression: "#id = :id",
        ExpressionAttributeNames:{
            "#id": "id"
        },
        ExpressionAttributeValues: {
            ":id": _id
        }
    };

    try {
        const results = await docClient.query(params).promise();
        return results.Items;
    }catch(e){
        console.log(e)
        return []
    }
}
```

<br/>

##  DynamoDB 삭제

<hr/>

Amazon DynamoDB 테이블에서 기존 항목을 삭제 합니다.

<u><b>기본적으로, Amazon DynamoDB는 Key를 사용하여 한 번에 하나의 단일 항목만 삭제할 수 있습니다.</b></u>

따라서, 일반 RDB를 사용하는 것처럼 삭제를 하기위해선 위의 Select 문으로 Key를 조회한 뒤, loop문을 사용하여, Key에 해당하는 단일 항목을 하나씩 삭제해야 합니다.

<u><b>마찬가지로, 예측가능한 프로그래밍을 위해 async, await구문을 사용하여, 순차 처리를 보장하는 것도 잊지 말아야합니다.</b></u>

``` javascript

export deleteDatas = async (_id) => {
    try {

        const deleteItems = await selectDatas(_id);
        deleteItems.forEach((e, i)=>{
            console.log(e.id)
            console.log(deleteData(e.id))
        })
        return true        
    }catch(e){
        console.log(e)
        return false
    }
}

const deleteData = async (_id) => {
    const params = {
        TableName: '테이블명',
        Key:{
            "id": _id,
        }
    };
    await docClient.delete(params).promise();    
}
```

<br/>

##  AWS DynamoDB 기본 쿼리 사용법

<hr/>

👉 [AWS DynamoDB 기본 쿼리 사용법](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.NodeJs.html)