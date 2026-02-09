# __PROJECT_NAME__ Frontend Dockerfile

FROM node:20-alpine

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm install

# 소스 코드 복사
COPY . .

# 빌드 (프로덕션)
# RUN npm run build

# 개발 서버 실행
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
