#!/bin/bash
#
# Project Sunshine - 자동 스케줄러 제거 스크립트
#
# install_scheduler.sh --uninstall 의 단축 버전
#
# Author: 송지영 대리
# Date: 2026-01-30

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/install_scheduler.sh" --uninstall
