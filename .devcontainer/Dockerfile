FROM python:3.14-slim

# ロケールとタイムゾーンの設定
ENV LANG=ja_JP.UTF-8
ENV LANGUAGE=ja_JP:ja
ENV LC_ALL=ja_JP.UTF-8
ENV TZ=Asia/Tokyo

# Install system packages as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales tzdata \
    vim git curl ca-certificates \
    libpq-dev gcc python3-dev \
    postgresql-client \
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ロケールの生成
RUN sed -i '/ja_JP.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen ja_JP.UTF-8 && \
    update-locale LANG=ja_JP.UTF-8

# タイムゾーンの設定
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install Node.js (required for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y nodejs \
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install GitHub CLI
RUN mkdir -p -m 755 /etc/apt/keyrings \
	&& curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& mkdir -p -m 755 /etc/apt/sources.list.d \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& apt update \
	&& apt install gh -y

# for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
         xvfb \
         xauth \
         libglib2.0-0t64 \
         libnspr4 \
         libnss3 \
         libdbus-1-3 \
         libatk1.0-0t64 \
         libatk-bridge2.0-0t64 \
         libcups2t64 \
         libxcb1 \
         libxkbcommon0 \
         libatspi2.0-0t64 \
         libx11-6 \
         libxcomposite1 \
         libxdamage1 \
         libxext6 \
         libxfixes3 \
         libxrandr2 \
         libgbm1 \
         libcairo2 \
         libpango-1.0-0 \
         libasound2 \
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install uv as root and make it available system-wide
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
 && mv /root/.local/bin/uv /usr/local/bin/uv \
 && chmod +x /usr/local/bin/uv

# Create vscode user
RUN groupadd --gid 1000 vscode \
 && useradd --uid 1000 --gid vscode --shell /bin/bash --create-home vscode

USER vscode
WORKDIR /workspace

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/vscode/.local/bin:${PATH}"
