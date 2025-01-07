document.addEventListener("DOMContentLoaded", () => {
    const flashMessagesElement = document.getElementById("flash-messages");
    if (flashMessagesElement) {
        const flashMessages = JSON.parse(flashMessagesElement.textContent);
        flashMessages.forEach(([category, message]) => {
            if (category === "success") {
                Swal.fire({
                    icon: "success",
                    title: message,
                    showConfirmButton: true,
                });
            } else if (category === "error") {
                Swal.fire({
                    icon: "error",
                    title: message,
                    showConfirmButton: true,
                });
            }
        });
    }
  });