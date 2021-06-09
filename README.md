#  전지호 기술블로그

## 기술블로그 로컬에서 띄우기(윈도우,맥os)

<hr/>

``` shell
docker-compose up
```
브라우저를 열고 127.0.0.1:4000에 접속하세요.

## 기술 블로그 포스트 작성 Rule

<hr/>

``` md

<!-- 0. 시작 제목은 (h1)#과 한줄 요약으로-->
# 제목입력
> 한줄요약 

<!-- 1. (h2)##에 해당하는 제목 줄 입력 시, 언더바 사용 -->
## 제목입력
<hr/>

<!-- 2. 단락이 끝나는 마지막에 항상 줄 바꿈 삽입 -->
<br/>

<!-- 3. 이미지와 코드 길이에 맞추와 toc 사용 -->
코드블럭이나 이미지가 클 시
toc: false
코드블럭이나 이미지가 작을 시
toc: true

<!-- 4. 가독성을 위해 줄 바꿈 자주사용, 짧은 구문으로 사용 -->
아버지 가방에 들어가시고 저녁을 잡수신다.

아버지 가방에 들어가신다.
저녁을 잡수신다.

<!-- 5. 첫 리스트는 들여쓰지 하지 않음-->
리스트입니다
- 첫 번째 항목
- 두 번째 항목
    - 두 번째 항목의 서브 항목

<!-- 6. 문장 강조는 볼드와 언더라인, 단어 강조는 ``-->
<u><b>문장을 강조합니다.</b></u>
`단어`

```