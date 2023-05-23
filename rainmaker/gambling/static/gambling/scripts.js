// declare a global variable for csrf_token
const CSRF_TOKEN = document.querySelector("[name=csrfmiddlewaretoken]").value;

// add functions to buttons when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // if the loaded page is index, run validateBet()
  const index_page = document.getElementById("page-identifier");
  if (index_page) validateBet();

  // Use buttons to request forecast, follow/unfollow, place bet
  const forecastButton = document.querySelector("#forecast");
  if (forecastButton) forecastButton.addEventListener("click", forecast);

  const watchlistButtons = document.querySelectorAll(".btn-follow");
  if (watchlistButtons) {
    for (let i = 0; i < watchlistButtons.length; i++) {
      watchlistButtons[i].addEventListener("click", watch);
    }
  }

  // if balance is shown (i.e., user authenticated), then add function to betButtons
  let balance = document.querySelector("#user-balance");
  if (balance) {
    balance = parseFloat(document.querySelector("#user-balance").innerText);
    const betButtons = document.querySelectorAll(".btn-bet");
    if (betButtons) {
      for (let i = 0; i < betButtons.length; i++) {
        if (balance <= 0) {
          betButtons[i].addEventListener("click", negativePrompt);
        } else {
          betButtons[i].addEventListener("click", placeBet);
        }
      }
    }
  }

  // set the default value of date picker to today
  const datePicker = document.querySelector("#date");
  if (datePicker) {
    Date.prototype.toDateInputValue = function () {
      let local = new Date(this);
      local.setMinutes(this.getMinutes() - this.getTimezoneOffset());
      return local.toJSON().slice(0, 10);
    };
    datePicker.value = new Date().toDateInputValue();
  }
});

// validate the bets shown on index page
const validateBet = () => {
  // identify pools that are active and need to be validated
  const status_flags = document.querySelectorAll(".pool-status");
  let pool = [];
  for (let i = 0; i < status_flags.length; i++) {
    if (status_flags[i].dataset.status === "True") {
      const hour = status_flags[i].dataset.hour;
      const date = status_flags[i].dataset.date;
      let datetime = Date.parse(`${date} ${hour}:00:00 GMT`);
      // if hour is zero (i.e., timeslot = 23:00-23:59, of which the actual weather will be in the 00:00 timeslot of next day),
      // add one day (86,400,000 ms) to datetime
      if (hour === "0") {
        datetime += 86400000;
      }

      pool.push({
        id: status_flags[i].dataset.pool,
        lat: status_flags[i].dataset.lat,
        long: status_flags[i].dataset.long,
        date: date,
        hour: hour,
        datetime: datetime,
      });
    }
  }

  // for each pool in array, check if the date and hour have come; only keep the due pools in array
  const time_now = Date.now();
  pool = pool.filter((item) => item.datetime < time_now);
  console.log("active, due pools:", pool);

  // run a GET to fetch the current weather for each pool remaining in array
  for (let i = 0; i < pool.length; i++) {
    fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${pool[i].lat}&longitude=${pool[i].long}&hourly=precipitation&past_days=7`
    )
      .then((response) => response.json())
      .then((jsonFB) => {
        const d = new Date(pool[i].datetime);
        const yyyy = d.getFullYear();
        const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
        const dd = String(d.getUTCDate()).padStart(2, "0");
        const hh = String(pool[i].hour).padStart(2, "0");
        const qDate = `${yyyy}-${mm}-${dd}T${hh}:00`;
        console.log(`pool #${i} qDate: ${qDate}`);
        // console.log(`pool #${i} response: ${jsonFB}`);
        let hourly = jsonFB.hourly;
        console.log(`pool_id picks index ${hourly.time.indexOf(qDate)}`);
        // make precipitation a string in case it is zero
        let precipitation = String(
          hourly.precipitation[hourly.time.indexOf(qDate)]
        );
        console.log(`pool_id ${pool[i].id} precipitation: ${precipitation}`);

        // if precipitation is found, update the pool's html and css
        if (precipitation) {
          const card = document.getElementById(`card-${pool[i].id}`);
          card.classList.replace("bg-white", "bg-dark");
          card.classList.replace("text-dark", "text-white");
          document.getElementById(`span-${pool[i].id}`).innerText = "Closed";
          const betButton = document.getElementById(`button-${pool[i].id}`);
          if (betButton) betButton.remove();

          if (parseFloat(precipitation) > 0) {
            console.log("House won");
          } else {
            console.log("Punter won");
          }
          let winner = parseFloat(precipitation) > 0 ? "House" : "Punter";
          const result_box = document.createElement("div");
          result_box.className = "grow";
          result_box.innerHTML = `
          <p class='display-4 mt-2 mb-0 text-center'>The <strong class='text-danger'>${winner}</strong> won!!!</p>
          <p class="text-right m-0 font-italic">Thus spoke Rainmaker</p>
          `;
          card.append(result_box);
          result_box.style.animationPlayState = "running";

          // if balance is shown (i.e., user authenticated), then grab the user_id
          let user_id = -1;
          let balance = document.querySelector("#user-balance");
          if (balance) {
            user_id = balance.dataset.user;
          }

          // update the pool's status and winner on the backend
          fetch("/validate", {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": CSRF_TOKEN,
            },
            body: JSON.stringify({
              pool_id: pool[i].id,
              pool_winner: winner,
              user_id: user_id,
            }),
          })
            .then((response) => response.json())
            .then((data) => {
              // if balance is shown, then update it with the user's latest balance
              if (balance) {
                balance.innerText = parseFloat(data.message);
              }
            });
        } else {
          console.log(
            `Precipitation date for pool-id ${pool[i].id} cannot be found.`
          );
        }
      });
  }
};

// get a forecast from Open-Meteo on Odds page
const forecast = () => {
  // clear the result field regardless if the forecast works:
  const result = document.querySelector("#result");
  result.innerHTML = "";

  const lat = document.querySelector("#latitude").value;
  const long = document.querySelector("#longitude").value;
  const dateStr = document.querySelector("#date").value;
  const fDate = Date.parse(dateStr);
  const fTime = document.querySelector("#time").value;
  const fHour = fTime.split(":")[0];

  // run fetch only if the long/lat is number between -90 & 90, date is a valid date and hour is between 0 and 23
  if (
    !isNaN(lat) &&
    lat >= -90 &&
    lat <= 90 &&
    !isNaN(long) &&
    long >= -90 &&
    long <= 90 &&
    !isNaN(fDate) &&
    !isNaN(fHour) &&
    fHour >= 0 &&
    fHour <= 23
  ) {
    fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${long}&hourly=precipitation_probability`
    )
      .then((feedback) => feedback.json())
      .then((jsonFB) => {
        // form a string in ISO 8601 format, the minute doesn't matter and therefore is 00
        const d = new Date(fDate);
        const yyyy = d.getFullYear();
        const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
        const dd = String(d.getUTCDate()).padStart(2, "0");
        const qDate = `${yyyy}-${mm}-${dd}T${fHour}:00`;

        console.log(jsonFB);
        let hourly = jsonFB.hourly;
        let chance =
          hourly.precipitation_probability[hourly.time.indexOf(qDate)];

        const result_box = document.querySelector("#result");
        result_box.innerHTML = `
        <div class="mx-5 px-2">
          <p class="exclamation-font text-warning font-weight-bold">The probability of precipitation is . . . <span class="brand-font">${chance}%</span></p>  
          <p class="text-right text-white font-italic">Thus spoke Rainmaker</p>
          <hr>
          </div>
        `;
        result_box.style.animationPlayState = "running";
      });
  }

  return false;
};

const watch = () => {
  const clickedBut = event.target;
  const pool = clickedBut.dataset.pool;
  const user = clickedBut.dataset.user;
  console.log(`user-${user} watching pool pool-${pool}`);

  fetch("/watchlist", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN,
    },
    body: JSON.stringify({
      user_id: user,
      pool_id: pool,
    }),
  })
    .then((feedback) => feedback.json())
    .then((jsonFB) => {
      const watchCount = document.querySelector("#watch-count");
      let count = parseInt(watchCount.innerText);
      // in case there is something wrong with the value of count
      if (isNaN(count)) count = 0;

      if (jsonFB.message === "followed") {
        clickedBut.innerText = "Unwatch";
        count++;
      } else {
        clickedBut.innerText = "Watch";
        count--;
      }

      // update the watch count
      watchCount.innerText = count;
    });

  return false;
};

const negativePrompt = () => {
  const pool_id = event.target.dataset.pool;
  const hidden_div = document.querySelector(`#hidden-${pool_id}`);
  hidden_div.innerHTML = `
  <div class="alert alert-warning my-3">
    You can't place a bet unless your account balance is positive.
  </div>
  `;
  hidden_div.style.display = "block";
  hidden_div.style.animationPlayState = "running";
};

const placeBet = () => {
  const pool_id = event.target.dataset.pool;
  const hidden_div = document.querySelector(`#hidden-${pool_id}`);
  hidden_div.style.display = "block";
  hidden_div.style.animationPlayState = "running";

  document
    .querySelector(`#confirm-${pool_id}`)
    .addEventListener("click", confirmBet);
  return false;
};

const confirmBet = () => {
  const pool_id = event.target.dataset.pool;
  const user_balance = document.querySelector("#user-balance");
  let wager = document.querySelector(`#wager-${pool_id}`).value.trim();

  // the button responds only when the wager amount is a number greater than zero but not larger than the balance
  if (wager && !isNaN(wager)) {
    wager = parseFloat(wager);
    if (wager > 0 && wager <= parseFloat(user_balance.innerText)) {
      // post the bet to backend
      fetch("/wager", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF_TOKEN,
        },
        body: JSON.stringify({
          user_id: event.target.dataset.user,
          pool_id: pool_id,
          wager: wager,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          const hidden_div = document.querySelector(`#hidden-${pool_id}`);
          const message = data.message;

          if (message.toLowerCase().includes("accepted")) {
            // update the user's balance in header; the new balance is embedded in the message from backend
            const new_balance = message.slice(
              message.indexOf("New Balance:") + "New Balance:".length
            );
            console.log(new_balance);
            user_balance.innerText = new_balance;

            // update the bet button's innertText and remove its eventListener
            const betButton = document.querySelector(`#button-${pool_id}`);
            betButton.innerText = `Betted $${wager}`;
            betButton.classList.remove("btn-bet");
            betButton.removeEventListener("click", placeBet);

            // hide the hidden div again
            hidden_div.style.display = "none";
            hidden_div.style.animationPlayState = "paused";
          } else {
            // raise an alert if the transaction was rejected by backend
            hidden_div.innerHTML = `
            <div class="alert alert-danger my-3">
              <strong>Transaction Failed.</strong> ${message}
            </div>
            `;
          }
        });
    }
  }
  return false;
};
