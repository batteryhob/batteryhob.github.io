---
layout: page
title: Maintenance Guide
permalink: /maintenance/
published: false
---

# 유지보수 가이드 (Maintenance Guide)

이 문서는 블로그의 코드 구조와 유지보수 방법을 설명합니다.

## 다국어 지원 (Multilingual Support)

### 번역 텍스트 관리

모든 번역 텍스트는 `_data/i18n.yml` 파일에서 중앙 관리됩니다.

```yaml
ko:
  site_title: "배터리호 기술블로그"
  author_name: "배터리호"
  # ...

en:
  site_title: "BatteryHo Tech Blog"
  author_name: "BatteryHo"
  # ...
```

**새로운 번역 추가 방법:**
1. `_data/i18n.yml`에 새로운 키 추가
2. 템플릿에서 `{{ site.data.i18n[lang].key }}` 형식으로 사용

### 언어 감지

모든 페이지는 `page.lang` 변수를 사용하여 현재 언어를 감지합니다:
```liquid
{%- assign lang = page.lang | default: "ko" -%}
```

기본값은 한글(ko)이며, 영문 페이지는 front matter에 `lang: en`을 추가합니다.

## 재사용 가능한 컴포넌트

### 태그 링크 생성 (`_includes/tag_link.html`)

언어에 따라 올바른 태그 페이지 링크를 생성합니다.

**사용 예:**
```liquid
{% include tag_link.html tag="aws" lang=page.lang %}#aws</a>
```

이 컴포넌트는:
- 한글 페이지: `/tags/#aws` 링크 생성
- 영문 페이지: `/en/tags/#aws` 링크 생성

## 파일 구조

```
_data/
  i18n.yml              # 모든 번역 텍스트

_includes/
  tag_link.html         # 재사용 가능한 태그 링크 컴포넌트
  header.html           # 사이트 헤더 (다국어 지원)
  footer.html           # 사이트 푸터 (다국어 지원)
  main_banner.html      # 메인 페이지 배너 (다국어 지원)
  _members/
    ji_ho_jeon.html     # 작성자 정보 (다국어 지원, 스킬 태그 루프)

_layouts/
  home.html             # 홈 페이지 레이아웃
  post.html             # 포스트 레이아웃

tags.md                 # 한글 태그 페이지 (lang: ko)
en/
  tags.md               # 영문 태그 페이지 (lang: en)
```

## 일반적인 수정 작업

### 1. 사이트 제목 변경
`_data/i18n.yml`에서 `site_title` 수정

### 2. 작성자 소개 변경
`_data/i18n.yml`에서 `author_intro` 수정

### 3. 푸터 설명 변경
`_data/i18n.yml`에서 `footer_description` 수정

### 4. 메인 배너 명언 변경
`_data/i18n.yml`에서 `quote_line1`, `quote_line2` 수정

### 5. 스킬 태그 추가/제거
`_includes/_members/ji_ho_jeon.html`의 `skills` 변수 수정:
```liquid
{%- assign skills = "aws,docker,kubernetes,python,javascript,react,vue" | split: "," -%}
```

### 6. 새 포스트 작성
- 한글: `_posts/YYYY-MM-DD-제목.md` with `lang: ko`
- 영문: `_posts/YYYY-MM-DD-title.md` with `lang: en`

동일한 포스트의 번역은 `ref` 필드를 동일하게 설정:
```yaml
---
layout: post
title: 제목
lang: ko
ref: article-name
---
```

```yaml
---
layout: post
title: Title
lang: en
ref: article-name
---
```

## 코드 개선 사항 (이번 리팩토링)

1. **중복 제거**
   - 스킬 태그 목록이 2번 중복되던 것을 1번으로 축소 (60줄 → 28줄)
   - 언어별 분기 조건을 데이터 기반 접근으로 단순화

2. **중앙 집중식 관리**
   - 모든 번역 텍스트를 `_data/i18n.yml`로 이동
   - 텍스트 수정 시 한 곳만 변경하면 됨

3. **재사용성**
   - `tag_link.html` 컴포넌트로 태그 링크 로직 공통화
   - 새로운 곳에서도 동일한 로직 재사용 가능

4. **유지보수성**
   - 주석 추가로 코드 이해도 향상
   - 일관된 패턴으로 코드 예측 가능성 증가

## 트러블슈팅

### 번역이 표시되지 않을 때
1. `_data/i18n.yml`에 해당 키가 있는지 확인
2. 페이지의 `lang` 값이 올바른지 확인 (ko 또는 en)
3. Jekyll 서버 재시작

### 태그 링크가 잘못된 페이지로 이동할 때
1. 포스트의 `lang` 필드가 올바르게 설정되어 있는지 확인
2. `tag_link.html`에 `lang` 파라미터를 올바르게 전달했는지 확인

## 새로운 언어 추가하기

1. `_data/i18n.yml`에 새 언어 섹션 추가
2. 새 언어용 디렉토리 생성 (예: `ja/`)
3. `ja/index.md`, `ja/tags.md` 등 생성
4. 각 파일에 `lang: ja` 추가
5. 헤더에 언어 전환 링크 추가

## 참고사항

- Jekyll 빌드는 `_data`, `_includes`, `_layouts` 변경 시 자동으로 재빌드됩니다
- 로컬 테스트: `bundle exec jekyll serve`
- 캐시 문제 발생 시: `bundle exec jekyll clean && bundle exec jekyll serve`
