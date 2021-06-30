---
layout: post
title:  video 객체의 duration(영상의 길이)이 Infinity로 나올 때 올바른 영상길이를 얻는 방법
date:   2021-07-01 00:00:00 +0900
author: 전지호
tags: react graphql
excerpt: 크롬에서 Video에 접근해 영상 길이를 얻어올 때, 오류로 인하여 Infinity로 나타날 때가 있습니다.
use_math: false
toc: true
---


# duration이 Infinity로 나올 때, 어떻게 해야하지

> 오류가 Fix되기 전까지 다음의 코드를 사용하세요.

<br/>

## 해결방법

<hr/>

다음의 코드로 duration을 얻을 수 있습니다. (Type script)

``` typescript

//비디오의 시간 얻기(url: 영상의 주소)
getDuration = (url: any, next: any) =>{
    var _player = new Audio(url);
    _player.addEventListener("durationchange", function (e) {
        if (this.duration!==Infinity) {
            var duration = this.duration
            _player.remove();
            next(duration);
        };
    }, false);      
    _player.load();
    _player.currentTime = 24*60*60; //fake big time
    _player.volume = 0;
    _player.play();
    //waiting...
}

```
