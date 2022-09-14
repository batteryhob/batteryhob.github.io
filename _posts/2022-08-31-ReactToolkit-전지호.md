---
layout: post
title:  ReduxToolkit의 기본적인 사용법 알아보기
date:   2022-08-31 00:00:00 +0900
author: 전지호
tags: javascript react
excerpt: 최근 프로젝트를 진행하면서 사용된 ReduxToolkit의 기본적인 사용법을 알아보자.
use_math: false
toc: true
---


# React에서 ReduxToolkit을 사용하면서 상태 관리하기

> 기존의 Redux를 통한 상태관리는 React에서 가장 stable한 상태 관리 라이브러리지만, 너무 많은 보일러플레이트로 인해 소스의 볼륨을 늘리고, 비동기 통신에 대해 다른 라이브러리의 도움이 필요했던 것이 사실입니다.
React 18버전 이후, ReduxToolkit의 Redux에 대안이 될 수 있는지 최근 프로젝트를 진행하면서 사용한 기본적인 동작을 통해 알아보도록 하겠습니다.

<br/>

## 첫 번째, React 프로젝트에 ReduxToolkit 포함하기

<hr/>

다음의 명령어로 새로운 React Project를 생성 시, 다음의 명령어로 redux toolkit을 포함할 수 있습니다. 

``` shell
npx create-react-app my-app --template redux-typescript
```
<br/>

## 두 번째, Store와 Action을 관리하는 주요 요소

<hr/>

### 1. createSlice()

redux와 redux toolkit의 가장 큰 차이점이라고 볼 수 있는 부분이라고 생각할 수 있는 부분입니다.
createSlice()는 reducer를 만들때 필요한 항목들을 간소화하여, 사용할 수 있도록 설계된 부분으로
redux 보일러플레이트를 줄이고 redux안에 state의 불변성을 지키기 위한 로직을 사용할 수 있다.
createSlice는 RTK의 표준 로직이며, 이후 설명할 createAction과 createReducer를 포함합니다.

``` javascript
/// ...state 중략
export const slice = createSlice({
  name: "sourceGitBranchs",
  initialState,
  //reducer를 아래와 같이 추가합니다.
  reducers: {
    initFlag: (state) => {
      //state를 직접 바꾸는 것 같이 작성하여도 불변 상태가 유지됩니다. (redux에서는 ...operator를 통해 불변 상태 유지)
      state.flag = true;
    },
  },
});
```

아래에서 기존의 redux요소들이 어떻게 createSlice에 포함되었는지 알아봅시다.

### 2. createAction()
redux의 표준 로직에서는 아래와 같이 action을 명시하여, 사용하여 보일러플레이트가 많아지고, action을 관리해야 하는 파일도 늘어났지만,
redux toolkit에서는 이를 duck패턴으로 간편하게 사용할 수 있는 문법을 제공합니다.

``` javascript
//redux 패턴
const INCREMENT = 'counter/increment'
function increment(amount: number) {
  return {
    type: INCREMENT,
    payload: amount,
  }
}
const action = increment(3)

//rtk 패턴
const increment = createAction<number>('counter/increment')
```

creteAction을 reducer에서 사용할 경우, 위 항목을 생략하여 사용할 수 있습니다.


### 3. createReducer()
redux의 표준 로직에서는 switch 문법으로 action을 관리하여, state를 변경했지만, createReducer안에 builder.addCase기능을 통해 사용할 수 있습니다.

``` javascript
//redux 패턴
const initialState = { value: 0 }

function counterReducer(state = initialState, action) {
  switch (action.type) {
    case 'increment':
      return { ...state, value: state.value + 1 }
    case 'decrement':
      return { ...state, value: state.value - 1 }
    case 'incrementByAmount':
      return { ...state, value: state.value + action.payload }
    default:
      return state
  }
}

//rtk 패턴
import { createAction, createReducer } from '@reduxjs/toolkit'

interface CounterState {
  value: number
}

const increment = createAction('counter/increment')

const initialState = { value: 0 } as CounterState

const counterReducer = createReducer(initialState, (builder) => {
  builder
    .addCase(increment, (state, action) => {
      state.value++
    })
})
```

createReducer와 creteAction을 reducer에서 사용할 경우, 위 항목을 생략하여 아래와 같이 사용할 수 있습니다.

``` javascript
/// ...state 중략
export const slice = createSlice({
  name: "sourceGitBranchs",
  initialState,
  //reducer를 아래와 같이 추가합니다.
  reducers: {
    initFlag: (state) => {
      //state를 직접 바꾸는 것 같이 작성하여도 불변 상태가 유지됩니다. (redux에서는 ...operator를 통해 불변 상태 유지)
      state.flag = true;
    },
    //아래와 같이 createAction과 createReducer항목이 포함되어 있는 문법이 사용가능해 정말 많은 보일러플레이트가 생략됩니다.
    increment: (state) => {
      state.amount = 3;
    }
  },
});
```