// static/js/video_popup.js
document.addEventListener('DOMContentLoaded', function() {
    const videoViewerModal = new bootstrap.Modal(document.getElementById('videoViewerModal'));
    const videoPlayer = document.getElementById('videoPlayer');
    const modalTitle = document.getElementById('videoViewerModalLabel');
    const fullscreenBtn = document.getElementById('fullscreenBtn');

    document.querySelectorAll('.view-video-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const videoUrl = this.dataset.videoUrl;
            const videoTitle = this.dataset.videoTitle;

            modalTitle.textContent = videoTitle;
            videoPlayer.src = videoUrl;
            videoViewerModal.show();

            // Auto-play the video when the modal is shown
            videoPlayer.play().catch(error => {
                console.error("Autoplay prevented:", error);
                // Optionally, show a message to the user to manually play the video
            });
        });
    });

    // Pause video when modal is hidden
    videoViewerModal._element.addEventListener('hidden.bs.modal', function () {
        videoPlayer.pause();
        videoPlayer.currentTime = 0; // Reset video to start
    });

    // Fullscreen button functionality for the modal's video
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            if (videoPlayer.requestFullscreen) {
                videoPlayer.requestFullscreen();
            } else if (videoPlayer.mozRequestFullScreen) { /* Firefox */
                videoPlayer.mozRequestFullScreen();
            } else if (videoPlayer.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
                videoPlayer.webkitRequestFullscreen();
            } else if (videoPlayer.msRequestFullscreen) { /* IE/Edge */
                videoPlayer.msRequestFullscreen();
            }
        });
    }
});