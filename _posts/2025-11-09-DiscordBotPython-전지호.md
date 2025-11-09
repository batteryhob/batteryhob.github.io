---
layout: post
title: Python으로 디스코드 봇 만들기 - 초보자를 위한 완벽 가이드
date: 2025-11-09 00:00:00 +0900
author: 전지호
tags: python discord bot automation discord.py tutorial
excerpt: Python과 discord.py를 사용하여 나만의 디스코드 봇을 처음부터 만드는 방법을 배워봅시다. 코드 예제와 함께 실전 기능 구현까지 다룹니다.
use_math: false
toc: true
description: Python으로 디스코드 봇을 만드는 완벽 가이드 - discord.py 설치부터 실전 봇 기능 구현, 배포까지
lang: ko
ref: discord-bot-python
---

## 디스코드 봇이란?

디스코드 봇은 서버에서 자동화된 작업을 수행하는 프로그램입니다. 음악 재생, 관리 기능, 게임, 알림 등 다양한 용도로 사용됩니다.

Python은 디스코드 봇을 만들기에 가장 인기 있는 언어 중 하나입니다. **discord.py** 라이브러리 덕분에 초보자도 쉽게 시작할 수 있습니다.

## 왜 Python으로 디스코드 봇을 만드나요?

### Python의 장점

✅ **간결한 문법** - 배우기 쉽고 코드가 읽기 쉽습니다
✅ **강력한 라이브러리** - discord.py는 기능이 풍부하고 잘 문서화되어 있습니다
✅ **빠른 개발** - 적은 코드로 많은 기능을 구현할 수 있습니다
✅ **활발한 커뮤니티** - 문제가 생기면 도움을 쉽게 구할 수 있습니다

## 사전 준비사항

### 1. Python 설치

Python 3.8 이상이 필요합니다. [python.org](https://www.python.org/downloads/)에서 다운로드하세요.

```bash
# 버전 확인
python --version
# 또는
python3 --version
```

### 2. discord.py 설치

```bash
pip install discord.py
# 또는
pip3 install discord.py
```

### 3. Discord Developer Portal 설정

#### 봇 생성하기

1. [Discord Developer Portal](https://discord.com/developers/applications)에 접속
2. "New Application" 클릭
3. 봇 이름 입력 (예: "MyFirstBot")
4. 왼쪽 메뉴에서 "Bot" 선택
5. "Add Bot" 클릭
6. "Reset Token"을 클릭하여 토큰 복사 (⚠️ 절대 공유하지 마세요!)

#### 봇 권한 설정

1. "OAuth2" > "URL Generator" 선택
2. "SCOPES"에서 `bot` 체크
3. "BOT PERMISSIONS"에서 필요한 권한 선택:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
4. 생성된 URL로 봇을 서버에 초대

## 첫 번째 봇 만들기

### 기본 구조

가장 간단한 봇부터 시작해봅시다.

```python
# bot.py
import discord
from discord.ext import commands

# 봇 인스턴스 생성
# intents는 봇이 어떤 이벤트를 받을지 설정
intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용 읽기 권한

bot = commands.Bot(command_prefix='!', intents=intents)

# 봇이 준비되었을 때 실행
@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인했습니다!')
    print(f'봇 ID: {bot.user.id}')
    print('------')

# 간단한 명령어: !안녕
@bot.command()
async def 안녕(ctx):
    await ctx.send(f'안녕하세요 {ctx.author.mention}님!')

# !핑 명령어 - 봇의 응답 속도 확인
@bot.command()
async def 핑(ctx):
    latency = round(bot.latency * 1000)  # ms 단위로 변환
    await ctx.send(f'🏓 퐁! 레이턴시: {latency}ms')

# 봇 토큰으로 실행
bot.run('YOUR_BOT_TOKEN_HERE')
```

### 환경 변수로 토큰 관리 (보안)

토큰을 코드에 직접 넣는 것은 위험합니다. `.env` 파일을 사용하세요.

#### 1. python-dotenv 설치

```bash
pip install python-dotenv
```

#### 2. .env 파일 생성

```env
# .env
DISCORD_TOKEN=your_actual_bot_token_here
```

#### 3. .gitignore에 추가

```
# .gitignore
.env
```

#### 4. 수정된 bot.py

```python
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인했습니다!')

# 봇 실행
bot.run(TOKEN)
```

## 실전 기능 구현

### 1. 환영 메시지 봇

새로운 멤버가 서버에 들어오면 환영 메시지를 보냅니다.

```python
@bot.event
async def on_member_join(member):
    # 시스템 채널에 환영 메시지 전송
    channel = member.guild.system_channel
    if channel is not None:
        embed = discord.Embed(
            title='🎉 새로운 멤버!',
            description=f'{member.mention}님, 환영합니다!',
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name='멤버 수', value=f'{member.guild.member_count}명')
        await channel.send(embed=embed)
```

### 2. 정보 명령어

서버 또는 유저 정보를 보여줍니다.

```python
@bot.command()
async def 서버정보(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f'{guild.name} 정보',
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name='서버 ID', value=guild.id, inline=False)
    embed.add_field(name='생성일', value=guild.created_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='멤버 수', value=guild.member_count, inline=True)
    embed.add_field(name='채널 수', value=len(guild.channels), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def 유저정보(ctx, member: discord.Member = None):
    member = member or ctx.author  # 멤버 지정 안 하면 자기 자신

    embed = discord.Embed(
        title=f'{member.name}의 정보',
        color=member.color
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name='닉네임', value=member.display_name, inline=True)
    embed.add_field(name='ID', value=member.id, inline=True)
    embed.add_field(name='가입일', value=member.joined_at.strftime('%Y-%m-%d'), inline=False)

    roles = [role.mention for role in member.roles if role.name != '@everyone']
    if roles:
        embed.add_field(name='역할', value=', '.join(roles), inline=False)

    await ctx.send(embed=embed)
```

### 3. 관리 명령어

메시지 삭제, 멤버 관리 등의 기능입니다.

```python
@bot.command()
@commands.has_permissions(manage_messages=True)
async def 청소(ctx, amount: int):
    """메시지 삭제 (관리자 전용)"""
    if amount < 1 or amount > 100:
        await ctx.send('1~100 사이의 숫자를 입력하세요.')
        return

    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'✅ {len(deleted)-1}개의 메시지를 삭제했습니다.', delete_after=5)

@bot.command()
@commands.has_permissions(kick_members=True)
async def 추방(ctx, member: discord.Member, *, reason='사유 없음'):
    """멤버 추방 (관리자 전용)"""
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention}님을 추방했습니다. 사유: {reason}')

# 권한 없을 때 에러 처리
@청소.error
@추방.error
async def permission_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ 이 명령어를 사용할 권한이 없습니다.')
```

### 4. 재미있는 기능

주사위, 동전 던지기 등의 게임 기능입니다.

```python
import random

@bot.command()
async def 주사위(ctx, dice: str = '1d6'):
    """주사위 굴리기 (예: !주사위 2d20)"""
    try:
        rolls, sides = map(int, dice.split('d'))
        if rolls > 100 or sides > 1000:
            await ctx.send('너무 큰 숫자입니다!')
            return

        results = [random.randint(1, sides) for _ in range(rolls)]
        total = sum(results)

        embed = discord.Embed(title='🎲 주사위 결과', color=discord.Color.gold())
        embed.add_field(name='주사위', value=dice, inline=True)
        embed.add_field(name='결과', value=', '.join(map(str, results)), inline=True)
        embed.add_field(name='합계', value=total, inline=True)

        await ctx.send(embed=embed)
    except:
        await ctx.send('형식: !주사위 XdY (예: !주사위 2d6)')

@bot.command()
async def 동전(ctx):
    """동전 던지기"""
    result = random.choice(['앞면 🪙', '뒷면 🌑'])
    await ctx.send(f'동전 결과: **{result}**')

@bot.command()
async def 선택(ctx, *choices: str):
    """여러 선택지 중 하나를 랜덤으로 선택"""
    if len(choices) < 2:
        await ctx.send('최소 2개 이상의 선택지를 입력하세요.')
        return

    choice = random.choice(choices)
    await ctx.send(f'🎯 선택: **{choice}**')
```

### 5. 투표 시스템

간단한 투표 기능입니다.

```python
@bot.command()
async def 투표(ctx, question: str, *options):
    """투표 생성 (최대 10개 옵션)"""
    if len(options) > 10:
        await ctx.send('옵션은 최대 10개까지 가능합니다.')
        return
    if len(options) < 2:
        await ctx.send('최소 2개의 옵션이 필요합니다.')
        return

    # 이모지 숫자
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    description = '\n'.join([f'{emojis[i]} {option}' for i, option in enumerate(options)])

    embed = discord.Embed(
        title=f'📊 투표: {question}',
        description=description,
        color=discord.Color.blue()
    )
    embed.set_footer(text=f'투표 생성자: {ctx.author.display_name}')

    poll_message = await ctx.send(embed=embed)

    # 반응 추가
    for i in range(len(options)):
        await poll_message.add_reaction(emojis[i])
```

### 6. 타이머 및 알림

```python
import asyncio

@bot.command()
async def 타이머(ctx, seconds: int, *, message='시간이 다 됐습니다!'):
    """타이머 설정 (초 단위)"""
    if seconds > 3600:  # 1시간 제한
        await ctx.send('타이머는 최대 1시간(3600초)까지 설정 가능합니다.')
        return

    await ctx.send(f'⏰ {seconds}초 타이머를 시작합니다.')
    await asyncio.sleep(seconds)
    await ctx.send(f'{ctx.author.mention} {message}')
```

## Cogs를 사용한 코드 구조화

봇이 커지면 코드를 모듈화하는 것이 좋습니다. Cogs를 사용하면 기능별로 파일을 분리할 수 있습니다.

### 프로젝트 구조

```
discord_bot/
├── bot.py              # 메인 파일
├── cogs/               # Cogs 폴더
│   ├── fun.py         # 재미 기능
│   ├── moderation.py  # 관리 기능
│   └── info.py        # 정보 기능
├── .env               # 환경 변수
└── requirements.txt   # 의존성
```

### Cog 예제: fun.py

```python
# cogs/fun.py
import discord
from discord.ext import commands
import random

class Fun(commands.Cog):
    """재미있는 명령어들"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def 주사위(self, ctx, dice: str = '1d6'):
        """주사위 굴리기"""
        try:
            rolls, sides = map(int, dice.split('d'))
            results = [random.randint(1, sides) for _ in range(rolls)]
            await ctx.send(f'🎲 결과: {results} (합계: {sum(results)})')
        except:
            await ctx.send('형식: !주사위 XdY')

    @commands.command()
    async def 동전(self, ctx):
        """동전 던지기"""
        result = random.choice(['앞면 🪙', '뒷면 🌑'])
        await ctx.send(f'결과: **{result}**')

# Cog 로드 함수
async def setup(bot):
    await bot.add_cog(Fun(bot))
```

### 메인 파일에서 Cogs 로드

```python
# bot.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인했습니다!')
    print('------')

# Cogs 로드
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = filename[:-3]  # .py 제거
            await bot.load_extension(f'cogs.{cog_name}')
            print(f'Loaded cog: {cog_name}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

# 봇 실행
asyncio.run(main())
```

## 에러 처리

봇이 안정적으로 동작하려면 에러 처리가 중요합니다.

```python
@bot.event
async def on_command_error(ctx, error):
    """전역 에러 핸들러"""

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'❌ 필수 인자가 누락되었습니다: `{error.param.name}`')

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ 이 명령어를 사용할 권한이 없습니다.')

    elif isinstance(error, commands.CommandNotFound):
        # 명령어를 찾지 못했을 때는 무시
        pass

    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'⏳ 쿨다운 중입니다. {error.retry_after:.1f}초 후에 다시 시도하세요.')

    else:
        print(f'Unhandled error: {error}')
        await ctx.send('❌ 명령어 실행 중 오류가 발생했습니다.')
```

## 봇 배포하기

### 옵션 1: 로컬에서 실행

개발 중에는 로컬에서 실행하면 됩니다.

```bash
python bot.py
```

### 옵션 2: 클라우드 서버 (24/7 운영)

#### Replit (무료, 간단)

1. [Replit](https://replit.com/) 가입
2. New Repl 생성 (Python)
3. 코드 업로드
4. Secrets에 `DISCORD_TOKEN` 추가
5. Run 버튼 클릭

#### Railway / Render (무료/유료)

```yaml
# railway.json / render.yaml
build:
  - pip install -r requirements.txt
start:
  - python bot.py
```

#### DigitalOcean / AWS (유료, 전문적)

Ubuntu 서버에서 실행:

```bash
# 의존성 설치
sudo apt update
sudo apt install python3 python3-pip

# 봇 코드 복사
git clone your-repo-url
cd discord_bot

# 패키지 설치
pip3 install -r requirements.txt

# 백그라운드에서 실행 (screen 사용)
screen -S discord_bot
python3 bot.py
# Ctrl+A+D로 detach
```

### requirements.txt 생성

```txt
discord.py>=2.0.0
python-dotenv>=0.19.0
```

## 봇을 계속 실행하는 방법

### systemd 서비스 (Linux)

```ini
# /etc/systemd/system/discordbot.service
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

활성화:

```bash
sudo systemctl enable discordbot
sudo systemctl start discordbot
sudo systemctl status discordbot
```

### Docker 사용

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  bot:
    build: .
    restart: always
    env_file:
      - .env
```

실행:

```bash
docker-compose up -d
```

## 모범 사례 (Best Practices)

### 1. 토큰 보안

- ✅ `.env` 파일 사용
- ✅ `.gitignore`에 `.env` 추가
- ❌ 코드에 토큰 직접 입력 금지
- ❌ 공개 저장소에 토큰 업로드 금지

### 2. Rate Limiting

Discord API는 요청 제한이 있습니다. 쿨다운을 사용하세요.

```python
from discord.ext import commands

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)  # 5초당 1회
async def 명령어(ctx):
    await ctx.send('쿨다운이 있는 명령어!')
```

### 3. 로깅

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
```

### 4. 데이터베이스 사용

지속적인 데이터 저장이 필요하면 데이터베이스를 사용하세요.

```python
import sqlite3

# 간단한 SQLite 예제
conn = sqlite3.connect('bot_data.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0
    )
''')
conn.commit()
```

## 더 배우기

### 유용한 리소스

- [discord.py 공식 문서](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [discord.py GitHub](https://github.com/Rapptz/discord.py)

### 다음 단계

봇을 만들었다면 이런 기능들을 추가해보세요:

1. **데이터베이스 연동** - 유저 포인트, 레벨링 시스템
2. **API 통합** - 날씨, 뉴스, 게임 정보
3. **음악 봇** - YouTube, Spotify 연동
4. **대시보드** - 웹 인터페이스로 봇 관리
5. **AI 챗봇** - OpenAI API 연동

## 마치며

Python으로 디스코드 봇을 만드는 것은 생각보다 쉽습니다. 이 가이드의 코드를 따라하면 기본적인 봇을 만들 수 있고, 여기서부터 자신만의 기능을 추가할 수 있습니다.

### 핵심 요점

1. **discord.py**는 강력하고 사용하기 쉬운 라이브러리입니다
2. **토큰 보안**은 매우 중요합니다
3. **Cogs**를 사용하면 코드를 깔끔하게 정리할 수 있습니다
4. **에러 처리**와 **쿨다운**으로 안정적인 봇을 만들 수 있습니다

디스코드 봇 개발을 즐기세요! 🤖✨

---

질문이나 제안이 있다면 댓글로 남겨주세요.
