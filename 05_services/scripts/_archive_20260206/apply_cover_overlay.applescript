-- PPT 템플릿을 사용한 표지 생성 AppleScript
-- Keynote 사용

on run argv
    set coverImagePath to item 1 of argv
    set titleText to item 2 of argv
    set outputPath to item 3 of argv
    set templatePath to "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/templates/text_guide.pptx"

    tell application "Keynote"
        activate

        -- 템플릿 열기
        open POSIX file templatePath
        delay 1

        set theDoc to front document
        set theSlide to slide 1 of theDoc

        -- 이미지 추가하고 맨 뒤로
        tell theSlide
            -- 기존 이미지 찾아서 삭제 (있다면)
            -- 새 이미지 추가
            set newImage to make new image with properties {file:POSIX file coverImagePath}
            set width of newImage to 1080
            set height of newImage to 1080
            set position of newImage to {0, 0}

            -- 맨 뒤로 보내기
            -- Note: Keynote API 제한으로 정확한 순서 제어가 어려울 수 있음
        end tell

        -- 텍스트 변경
        tell theSlide
            repeat with aItem in every text item
                set object text of aItem to titleText
            end repeat
        end tell

        -- PNG로 내보내기
        export theDoc to POSIX file outputPath as PNG with properties {image format:PNG, export style:IndividualSlides}

        close theDoc without saving
    end tell
end run
