#!/bin/bash
#
# Project Sunshine - launchd 설정 스크립트
# Instagram 통계 자동 수집 데몬 설치/제거
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.sunshine.stats.plist"
PLIST_SRC="${SCRIPT_DIR}/${PLIST_NAME}"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_NAME}"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "${SCRIPT_DIR}")")")"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}  Project Sunshine - Stats Daemon${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

check_requirements() {
    print_info "요구사항 확인 중..."

    # Python 확인
    if ! command -v python3 &> /dev/null; then
        print_error "python3가 설치되어 있지 않습니다."
        exit 1
    fi
    print_success "Python3: $(python3 --version)"

    # 프로젝트 파일 확인
    if [ ! -f "${PROJECT_ROOT}/services/scripts/stats_collector_daemon.py" ]; then
        print_error "stats_collector_daemon.py를 찾을 수 없습니다."
        exit 1
    fi
    print_success "데몬 스크립트 확인"

    # plist 파일 확인
    if [ ! -f "${PLIST_SRC}" ]; then
        print_error "plist 파일을 찾을 수 없습니다: ${PLIST_SRC}"
        exit 1
    fi
    print_success "plist 파일 확인"
}

install_daemon() {
    print_header
    print_info "Instagram 통계 수집 데몬 설치 중..."

    check_requirements

    # LaunchAgents 디렉토리 확인
    mkdir -p "${HOME}/Library/LaunchAgents"

    # 기존 설치 제거
    if [ -f "${PLIST_DST}" ]; then
        print_info "기존 설치 제거 중..."
        launchctl unload "${PLIST_DST}" 2>/dev/null || true
        rm -f "${PLIST_DST}"
    fi

    # 로그 디렉토리 생성
    mkdir -p "${PROJECT_ROOT}/config/logs/stats"

    # plist 복사
    cp "${PLIST_SRC}" "${PLIST_DST}"
    print_success "plist 파일 복사 완료"

    # launchd 로드
    launchctl load "${PLIST_DST}"
    print_success "데몬 로드 완료"

    echo ""
    print_info "설치 완료! 매일 오전 9시에 통계가 수집됩니다."
    echo ""
    echo "  상태 확인:  launchctl list | grep sunshine"
    echo "  수동 실행:  launchctl start com.sunshine.stats"
    echo "  로그 확인:  tail -f ${PROJECT_ROOT}/config/logs/stats/launchd_stdout.log"
    echo "  제거:       $0 uninstall"
    echo ""
}

uninstall_daemon() {
    print_header
    print_info "Instagram 통계 수집 데몬 제거 중..."

    if [ -f "${PLIST_DST}" ]; then
        launchctl unload "${PLIST_DST}" 2>/dev/null || true
        rm -f "${PLIST_DST}"
        print_success "데몬 제거 완료"
    else
        print_info "설치된 데몬이 없습니다."
    fi
}

status_daemon() {
    print_header
    print_info "데몬 상태 확인 중..."

    if [ -f "${PLIST_DST}" ]; then
        print_success "plist 파일 존재: ${PLIST_DST}"

        if launchctl list | grep -q "com.sunshine.stats"; then
            print_success "데몬이 로드되어 있습니다."
            launchctl list com.sunshine.stats 2>/dev/null || true
        else
            print_info "데몬이 로드되지 않았습니다."
        fi
    else
        print_info "설치된 데몬이 없습니다."
    fi

    # 마지막 실행 로그
    if [ -f "${PROJECT_ROOT}/config/logs/stats/launchd_stdout.log" ]; then
        echo ""
        print_info "최근 로그 (마지막 10줄):"
        tail -10 "${PROJECT_ROOT}/config/logs/stats/launchd_stdout.log"
    fi
}

test_daemon() {
    print_header
    print_info "데몬 테스트 실행 (dry-run)..."

    cd "${PROJECT_ROOT}"
    python3 services/scripts/stats_collector_daemon.py --dry-run
}

run_now() {
    print_header
    print_info "데몬 즉시 실행..."

    cd "${PROJECT_ROOT}"
    python3 services/scripts/stats_collector_daemon.py --notify
}

show_help() {
    print_header
    echo "사용법: $0 [command]"
    echo ""
    echo "명령어:"
    echo "  install     데몬 설치 (launchd 등록)"
    echo "  uninstall   데몬 제거"
    echo "  status      데몬 상태 확인"
    echo "  test        테스트 실행 (dry-run)"
    echo "  run         즉시 실행 (알림 포함)"
    echo "  help        도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 install     # 데몬 설치"
    echo "  $0 status      # 상태 확인"
    echo "  $0 run         # 즉시 실행"
    echo ""
}

# 메인 실행
case "${1:-help}" in
    install)
        install_daemon
        ;;
    uninstall)
        uninstall_daemon
        ;;
    status)
        status_daemon
        ;;
    test)
        test_daemon
        ;;
    run)
        run_now
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "알 수 없는 명령어: $1"
        show_help
        exit 1
        ;;
esac
