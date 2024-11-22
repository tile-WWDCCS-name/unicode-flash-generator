import subprocess
import os


def add_music_to_video(video_path, audio_path, output_path):
    command = [
        'ffmpeg',
        '-stream_loop', '-1',   # 循环音频
        '-i', audio_path,       # 输入音频文件
        '-i', video_path,       # 输入视频文件
        '-c:v', 'copy',         # 视频编码
        '-c:a', 'copy',         # 音频编码
        '-shortest',            # 使输出文件的长度与视频相同
        output_path             # 输出文件路径
    ]

    subprocess.run(command)


if __name__ == '__main__':
    import argparse

    CUR_FOLDER = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(description="这是一个为视频添加BGM的脚本。")
    parser.add_argument('-vp', '--video_path', type=str,
                        default=os.path.join(CUR_FOLDER, "res.mp4"),
                        help='视频文件路径，默认为当前路径下的res.mp4文件。')
    parser.add_argument('-ap', '--audio_path', type=str,
                        default=os.path.join(CUR_FOLDER, "UFM.mp3"),
                        help='背景音乐文件路径，默认为当前路径下的UFM.mp3文件。')
    parser.add_argument('-op', '--output_path', type=str,
                        default=os.path.join(CUR_FOLDER, "with_audio.mp4"),
                        help='输出视频文件路径，默认为当前路径下的with_audio.mp4文件。')
    args = parser.parse_args()

    add_music_to_video(args.video_path, args.audio_path, args.output_path)
