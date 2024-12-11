document.addEventListener('DOMContentLoaded', function () {
  const CHECK_INTERVAL = 1000; // Check every 1s if elements appear
  let checkIntervalId;

  function animateCards() {
    const cards = document.querySelectorAll('.workflow-card');
    if (cards.length > 0) {
      anime({
        targets: cards,
        translateY: [50, 0],
        opacity: [0, 1],
        delay: anime.stagger(150, { start: 500 }),
        duration: 700,
        easing: 'easeOutBack',
        complete: function () {
          // After animation completes, remove inline transform so hover works
          cards.forEach((card) => {
            card.style.transform = '';
          });
          animateArrows();
        },
      });
    } else {
      console.log('No .workflow-card elements found yet.');
    }
  }

  function animateArrows() {
    // Arrow animations run once after cards appear
    anime({
      targets: '.arrow-1-2',
      width: [0, 100],
      easing: 'easeOutCubic',
      duration: 2000,
    });
    anime({
      targets: '.arrow-2-3',
      height: [0, 50],
      easing: 'easeOutCubic',
      duration: 2000,
      delay: 2000,
    });
    anime({
      targets: '.arrow-3-4',
      width: [0, 100],
      easing: 'easeOutCubic',
      duration: 2000,
      delay: 4000,
    });
    anime({
      targets: '.arrow-4-5',
      height: [0, 50],
      easing: 'easeOutCubic',
      duration: 2000,
      delay: 6000,
    });
  }

  function checkForElements() {
    const workflow = document.querySelector('#task-workflow');
    const cards = document.querySelectorAll('.workflow-card');
    if (workflow && cards.length > 0) {
      clearInterval(checkIntervalId);
      console.log(
        'Found #task-workflow and .workflow-card elements. Starting animations...'
      );
      animateCards();
    } else {
      console.log(
        'Waiting for #task-workflow and .workflow-card elements to appear...'
      );
    }
  }

  // Initially try to animate after DOMContentLoaded
  animateCards();

  // If no animations started because elements are missing, keep checking
  checkIntervalId = setInterval(checkForElements, CHECK_INTERVAL);
});
