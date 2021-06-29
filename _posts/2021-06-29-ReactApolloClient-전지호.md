---
layout: post
title:  React에서 ApolloClient를 이용해 Graphql서버 연동하기 
date:   2021-06-29 00:00:00 +0900
author: 전지호
tags: react graphql
excerpt: ApolloClient를 이용해 Graphql서버에 접근해 데이터를 가져와봅시다.
use_math: false
toc: true
---


# React에서 ApolloClient를 이용해 Graphql서버 연동하기

> ApolloClient를 활용한 기본 연동법에 대해 알아봅니다.

<br/>

## 첫 번째, React 프로젝트에 ApolloClient 설치하기

<hr/>

다음의 명령어로 ApolloClient를 설치합니다.

``` shell
npm install @apollo/client graphql
# or
yarn add @apollo/client graphql
```
<br/>

## 두 번째, index.js에 ApolloClient Provider설정하기

<hr/>

설치가 완료되었으면, index.js 혹은 index.tsx에 Provider 설정을 해야합니다.

``` javascript
import {
  ApolloClient,
  InMemoryCache,
  ApolloProvider,
  useQuery,
  gql
} from "@apollo/client";
```

다음 예제는, react-route, redux와 react-redux를 사용했을때 예제입니다.

``` javascript
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import * as serviceWorker from './serviceWorker';

//ApolloClient
import {
  ApolloClient,
  InMemoryCache,
  ApolloProvider,
  //useQuery, 이 페이지에서 사용하지 않습니다.
  //gql 이 페이지에서 사용하지 않습니다.
} from "@apollo/client";

//라우터
import { BrowserRouter } from 'react-router-dom';

//리덕스
import { Provider } from 'react-redux'
import { createStore, applyMiddleware  } from 'redux'
import { rootReducer  } from './redux/reducer'

//미들웨어-Redux
import ReduxThunk from 'redux-thunk';

const store = createStore(rootReducer, applyMiddleware(ReduxThunk)) //미들웨어 적용

const client = new ApolloClient({
  uri: 'GraphQL서버의 위치를 적어줍니다.',
  cache: new InMemoryCache()
});

ReactDOM.render(
  <React.StrictMode>
    <BrowserRouter>
      <Provider store={store} >
        <ApolloProvider client={client}>
          <App/>
        </ApolloProvider>
      </Provider>
    </BrowserRouter>    
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
```

Graphql서버를 연동하기 위한 준비가 완료되었습니다.

<br/>

## 세 번째, 쿼리 준비하기

<hr/>

Apollo Client에 포함되어 있는 gql를 이용해서 쿼리를 작성해야합니다. graphql의 자세한 쿼리 사용법은 다른 포스트를 참조해주세요.

보기 좋은 프로그래밍을 위하여 폴더를 분리해 쿼리만 모아놓는 js파일을 생성해서 사용합니다.

![쿼리분리](https://solution-userstats.s3.ap-northeast-1.amazonaws.com/techblogs/batteryho/graphql/%EC%BF%BC%EB%A6%AC%EB%B6%84%EB%A6%AC.JPG){ :popup }

query.js 안에 다음과 같이 작성합니다.


``` javascript
import { gql } from "@apollo/client";

export const GET_DATAS = gql`
    query GET_DATAS {
        datas {
            id
            contents
            regdate
        }
    }
`;
```
파라미터가 필요한 쿼리문도 하나 작성해봅시다.

``` javascript
import { gql } from "@apollo/client";

//파라미터 필요없음
export const GET_DATAS = gql`
    query GET_DATAS {
        datas {
            id
            contents
            regdate
        }
    }
`;

//파라미터 필요 시
export const GET_DATAS_PARAMETER = gql`
    query GET_DATAS_PARAMETER($id: Int!) {
        subdatas (id: $id) {
            id
            contents
            regdate
        }
    }
`;
```
위에서 쓴 쿼리를 Component에서 사용할 것 입니다.

<br/>

## 네 번째, Component에 데이터 바인딩 하기

<hr/>

Apollo Client에 포함되어 있는 useQuery라는 훅(Hook)을 이용해서 데이터를 바인딩할 것입니다.

다음과 같이 데이터바인딩이 가능합니다.

``` javascript
import React from 'react';

import { useQuery } from "@apollo/client";
import { GET_DATAS } from "../../../graphql/query";

const Sample: React.FC<any> = () => {

  const { data } = useQuery(GET_DATAS)

  return (
    <div>
      <ul>
        {
            data?datas.map((e:any,i:any)=>{
              return (
                  <li key={i}>
                    { e.id }
                  </li>
                )
            })
        }
      </ul>
    </div>
  )
}
```

##  참고문서

<hr/>

👉 [Get started with Apollo Client](https://www.apollographql.com/docs/react/get-started/)