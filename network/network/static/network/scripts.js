// declare a global variable for csrf_token
const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]').value;
// const CSRF_TOKEN = '{{ csrf_token }}';

// add functions to buttons when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to like/unlike and follow/unfollow
  const followButton = document.querySelector('#btn-follow');
  if (followButton) followButton.addEventListener('click', follow);
  
  const editButtons = document.querySelectorAll('.btn-edit');
  if (editButtons) {
    for (let i = 0; i < editButtons.length; i++) {
    editButtons[i].addEventListener('click', edit);
    }
  }
  
  const likeButtons = document.querySelectorAll('.btn-like');
  if (likeButtons) {
    for (let i = 0; i < likeButtons.length; i++) {
    likeButtons[i].addEventListener('click', like);
    }
  }
});

const edit = () => {
  const post_id = event.target.dataset.post;
  
  // get the original post and put it in textarea
  fetch(`/edit/${post_id}`)
    .then(feedback => feedback.json())
    .then(jsonFB => {
      document.querySelector(`#post-body-${post_id}`).innerHTML = 
      `
      <textarea autofocus class="form-control w-100" id="edited-post-${post_id}">${jsonFB.message}</textarea>
      <button type="submit" class="btn btn-primary btn-sm mt-2" onclick="saveEdit(${post_id})">
          Save
      </button>
      `;
    });
  

  // remove the edit button
  event.target.remove();

  return false;
}

// self-reminder: saveEdit() is included in the save btn when executing edit()
const saveEdit = (post_id) => {
  // put the edited post in post's body
  let editedPost = document.querySelector(`#edited-post-${post_id}`).value;
  document.querySelector(`#post-body-${post_id}`).innerHTML = 
  `
  <div class="card-text mb-2" id="post-body-${post_id}">${editedPost}</div>
  `;

  // re-create the edit button and append it to the card
  const editBut = document.createElement('button');
  editBut.classList.add('btn', 'btn-info', 'm-2', 'btn-edit');
  editBut.setAttribute('data-post', post_id);
  editBut.innerText = 'Edit';
  editBut.addEventListener('click', edit);
  document.querySelector(`#card-${post_id}`).append(editBut);

  // in case the editedPost is empty
  if (editedPost === '' || editedPost.trim() === '') editedPost = 'deleted';

  // fetch data to backend
  fetch('/edit', {
    method: 'PUT',
    headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': CSRF_TOKEN
    },
    body: JSON.stringify({
      post_id: post_id,
      post: editedPost,
    })
  })
}

const follow = () => {
  const clickedBut = event.target;
  const user = clickedBut.dataset.user;
  const victim = clickedBut.dataset.victim;

  fetch('/follow', {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': CSRF_TOKEN
    },
    body: JSON.stringify({
        user_id: user,
        victim_id: victim,
    })
  })
    .then(feedback => feedback.json())
    .then(jsonFB => {
      const stalkerCount = document.querySelector('#stalker-count');
      let count = parseInt(stalkerCount.innerText);
      // in case there is something wrong with the value of {{ victim.follower_count }}
      if (isNaN(count)) count = 0;

      if (jsonFB.message === 'followed') {
          clickedBut.innerText = 'Unfollow';
          count++;
      } else {
          clickedBut.innerText = 'Follow';
          count--;
      }
      
      // update the stalker count
      stalkerCount.innerText = count;
    })

  return false;
}

const like = () => {
  const clickedBut = event.target;
  const post = clickedBut.dataset.post;
  const user = clickedBut.dataset.user

  fetch('/like', {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': CSRF_TOKEN
    },
    body: JSON.stringify({
      post_id: post,
      user_id: user
    })
})
    .then(feedback => feedback.json())
    .then(jsonFB => {
      const likeCount = document.querySelector(`#like-count-${post}`);
      let count = parseInt(likeCount.innerText);
      // in case there is something wrong with the value of {{ post.like_count }}
      if (isNaN(count)) count = 0;

      // update the like/unlike button's text
      if (jsonFB.message === 'liked') {
          clickedBut.innerText = 'Unlike';
          count++;
      } else {
          clickedBut.innerText = 'Like';
          count--;
      }
      
      // update the like count
      likeCount.innerText = count;
    })

  return false;
}