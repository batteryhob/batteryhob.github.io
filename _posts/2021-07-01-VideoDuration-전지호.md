---
layout: post
title:  video 객체의 duration(영상의 길이)이 Infinity로 나올 때 올바른 영상길이를 얻는 방법
date:   2021-07-01 00:00:00 +0900
author: 전지호
tags: javascript html5 video frontend
excerpt: 크롬에서 Video에 접근해 영상 길이를 얻어올 때, 오류로 인하여 Infinity로 나타날 때가 있습니다. 이 문제의 원인과 해결 방법을 상세히 알아봅니다.
use_math: false
toc: true
---


# duration이 Infinity로 나올 때, 어떻게 해야하지

> 오류가 Fix되기 전까지 다음의 코드를 사용하세요.

<br/>

## 문제 상황

<hr/>

웹 개발을 하다 보면 HTML5 Video 요소를 사용해 영상을 재생하고, 해당 영상의 길이(duration)를 얻어와야 하는 경우가 자주 있습니다. 일반적으로 `video.duration` 속성을 사용하면 영상의 길이를 초 단위로 얻을 수 있습니다.

하지만 특정 상황에서 `video.duration`이 `Infinity`를 반환하는 문제가 발생합니다. 이 문제는 주로 다음과 같은 경우에 나타납니다:

### 1. 스트리밍 영상의 경우

라이브 스트리밍이나 일부 HLS(HTTP Live Streaming) 영상의 경우, 영상의 전체 길이가 정해져 있지 않기 때문에 `Infinity`를 반환합니다.

### 2. 메타데이터 로드 전 접근

영상의 메타데이터가 완전히 로드되기 전에 `duration`에 접근하면 `NaN` 또는 `Infinity`가 반환될 수 있습니다.

### 3. Chrome 브라우저 버그

Chrome 브라우저에서 특정 형식의 영상 파일(특히 WebM, 일부 MP4)에 대해 `duration`이 `Infinity`로 반환되는 버그가 보고되어 있습니다. 이 버그는 영상 파일의 인코딩 방식이나 메타데이터 구조에 따라 발생합니다.

### 4. Blob URL 사용 시

`URL.createObjectURL()`로 생성한 Blob URL을 사용하는 경우에도 이 문제가 발생할 수 있습니다.

<br/>

## 왜 이런 문제가 발생하는가?

<hr/>

HTML5 Video 요소는 영상 파일의 헤더에 포함된 메타데이터를 읽어 `duration` 값을 결정합니다. 그러나 일부 영상 파일은 다음과 같은 이유로 올바른 duration 정보를 제공하지 못합니다:

1. **가변 비트레이트(VBR) 인코딩**: 영상의 총 길이를 헤더에 기록하지 않는 경우
2. **스트리밍 최적화**: 라이브 스트리밍용으로 인코딩된 파일
3. **불완전한 메타데이터**: 인코딩 과정에서 duration 정보가 누락된 경우
4. **브라우저 파싱 오류**: 특정 코덱이나 컨테이너 형식에 대한 브라우저의 파싱 문제

<br/>

## 해결방법

<hr/>

다음의 코드로 duration을 얻을 수 있습니다. 이 방법은 Audio 객체를 활용하여 영상 파일의 실제 길이를 계산합니다.

### TypeScript 버전

``` typescript
// 비디오의 시간 얻기 (url: 영상의 주소)
getDuration = (url: any, next: any) => {
    var _player = new Audio(url);
    _player.addEventListener("durationchange", function (e) {
        if (this.duration !== Infinity) {
            var duration = this.duration;
            _player.remove();
            next(duration);
        };
    }, false);
    _player.load();
    _player.currentTime = 24 * 60 * 60; // fake big time (24시간)
    _player.volume = 0;
    _player.play();
    // waiting...
}
```

### JavaScript 버전

``` javascript
// 비디오의 시간 얻기 (url: 영상의 주소)
function getDuration(url, callback) {
    const audio = new Audio(url);

    audio.addEventListener("durationchange", function() {
        if (this.duration !== Infinity) {
            const duration = this.duration;
            audio.remove();
            callback(duration);
        }
    }, false);

    audio.load();
    audio.currentTime = 24 * 60 * 60; // 24시간을 초로 변환
    audio.volume = 0;
    audio.play().catch(() => {
        // autoplay 정책으로 인한 에러 무시
    });
}

// 사용 예시
getDuration('https://example.com/video.mp4', (duration) => {
    console.log(`영상 길이: ${duration}초`);
    console.log(`포맷: ${formatDuration(duration)}`);
});

// 시간 포맷 함수
function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
```

<br/>

## 코드 동작 원리

<hr/>

이 해결 방법이 작동하는 원리는 다음과 같습니다:

### 1. Audio 객체 활용

Video 요소 대신 Audio 객체를 사용합니다. 브라우저가 영상 파일의 오디오 트랙을 로드하면서 duration 정보를 올바르게 계산할 수 있습니다.

### 2. currentTime 트릭

`currentTime`을 매우 큰 값(24시간)으로 설정하면, 브라우저가 영상의 실제 길이를 찾기 위해 파일을 스캔합니다. 이 과정에서 올바른 duration 값이 계산됩니다.

### 3. durationchange 이벤트

`durationchange` 이벤트는 duration 값이 변경될 때마다 발생합니다. 처음에는 `Infinity`였다가 실제 값으로 변경되면 이 이벤트가 트리거됩니다.

### 4. 비동기 처리

이 방법은 비동기적으로 동작하므로, 콜백 함수나 Promise를 사용하여 결과를 처리해야 합니다.

<br/>

## Promise 기반 모던 버전

<hr/>

async/await를 사용하는 현대적인 방식으로 작성한 버전입니다:

``` javascript
function getVideoDuration(url) {
    return new Promise((resolve, reject) => {
        const audio = new Audio();

        const timeout = setTimeout(() => {
            audio.remove();
            reject(new Error('Duration fetch timeout'));
        }, 10000); // 10초 타임아웃

        audio.addEventListener("durationchange", function() {
            if (this.duration !== Infinity) {
                clearTimeout(timeout);
                audio.remove();
                resolve(this.duration);
            }
        });

        audio.addEventListener("error", function(e) {
            clearTimeout(timeout);
            audio.remove();
            reject(new Error('Failed to load audio'));
        });

        audio.src = url;
        audio.load();
        audio.currentTime = 24 * 60 * 60;
        audio.volume = 0;
        audio.play().catch(() => {});
    });
}

// 사용 예시
async function displayVideoDuration(videoUrl) {
    try {
        const duration = await getVideoDuration(videoUrl);
        console.log(`영상 길이: ${duration}초`);
    } catch (error) {
        console.error('영상 길이를 가져올 수 없습니다:', error);
    }
}
```

<br/>

## 대안적 해결 방법

<hr/>

위의 방법 외에도 다음과 같은 대안적 접근 방법들이 있습니다:

### 1. loadedmetadata 이벤트 활용

``` javascript
const video = document.createElement('video');
video.preload = 'metadata';

video.onloadedmetadata = function() {
    if (video.duration !== Infinity) {
        console.log(video.duration);
    }
};

video.src = 'video.mp4';
```

### 2. FFprobe 사용 (서버사이드)

서버 측에서 FFprobe를 사용하여 영상 메타데이터를 미리 추출하고, 클라이언트에 전달하는 방법도 있습니다.

### 3. 영상 재인코딩

문제가 되는 영상 파일을 FFmpeg 등으로 재인코딩하면 올바른 메타데이터가 기록됩니다.

<br/>

## 주의사항

<hr/>

1. **CORS 정책**: 외부 도메인의 영상에 접근할 때는 CORS 설정이 필요합니다.
2. **자동재생 정책**: 최신 브라우저들은 사용자 상호작용 없이 오디오/비디오 자동 재생을 제한합니다.
3. **메모리 관리**: 사용이 끝난 Audio/Video 객체는 반드시 제거해야 메모리 누수를 방지할 수 있습니다.
4. **타임아웃 처리**: 네트워크 문제나 파일 손상으로 인해 duration을 얻지 못할 수 있으므로, 적절한 타임아웃 처리가 필요합니다.

<br/>

## 결론

<hr/>

HTML5 Video의 `duration`이 `Infinity`를 반환하는 문제는 브라우저 버그나 영상 파일의 메타데이터 문제로 인해 발생합니다. 위에서 소개한 Audio 객체와 `currentTime` 트릭을 활용한 방법으로 대부분의 경우 해결할 수 있습니다.

이 문제는 Chrome 브라우저에서 특히 자주 발생하므로, 프로덕션 환경에서 영상 길이를 다룰 때는 항상 이러한 엣지 케이스를 고려한 방어적인 코드를 작성하는 것이 좋습니다.

도움이 되셨길 바랍니다!

<br/>

## 참고 자료

<hr/>

- [MDN Web Docs - HTMLMediaElement.duration](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/duration)
- [Chromium Bug Tracker - Video duration infinity issue](https://bugs.chromium.org/p/chromium/issues/list)
- [Stack Overflow - HTML5 video duration is "Infinity"](https://stackoverflow.com/questions/21522036/html-video-tag-duration-always-infinity)
