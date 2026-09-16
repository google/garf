FROM golang:1.26-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o grf .

FROM scratch AS prod
COPY --from=builder /app/grf /grf
ENTRYPOINT ["/grf"]
