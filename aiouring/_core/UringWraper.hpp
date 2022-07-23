#include <liburing.h>

class UringWraper {
private:
  struct io_uring ring;
  long long cnt;

public:
  ~UringWraper() {
    if (ring.ring_fd) {
      io_uring_queue_exit(&ring);
    }
  }
  inline int queue_init(unsigned entries, unsigned flags) {
    return io_uring_queue_init(entries, &ring, flags);
  }

  inline void wait_cqe(io_uring_cqe **cqe_ptr, double timeout_sec) {
    __kernel_timespec ts;
    ts.tv_sec = timeout_sec;
    ts.tv_nsec = (timeout_sec - ts.tv_sec) * 1e9;
    io_uring_wait_cqe_timeout(&ring, cqe_ptr, &ts);
  }
  inline void peek_cqe(io_uring_cqe **cqe_ptr) {
    io_uring_peek_cqe(&ring, cqe_ptr);
  }
  inline void cqe_seen(io_uring_cqe *cqe) { io_uring_cqe_seen(&ring, cqe); }

  inline long long do_read(int fd, char *buf, unsigned nbytes, __u64 offset) {
    io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_read(sqe, fd, buf, nbytes, offset);
    sqe->user_data = ++cnt;
    io_uring_submit(&ring);
    return cnt;
  }
  inline long long do_write(int fd, char *buf, unsigned nbytes, __u64 offset) {
    io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_write(sqe, fd, buf, nbytes, offset);
    sqe->user_data = ++cnt;
    io_uring_submit(&ring);
    return cnt;
  }
  inline long long do_poll_add(int fd, unsigned poll_mask) {
    io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_poll_add(sqe, fd, poll_mask);
    sqe->user_data = ++cnt;
    io_uring_submit(&ring);
    return cnt;
  }
  inline long long do_timeout(char *buf_16bytes, double timeout_sec) {
    ((__kernel_timespec *)buf_16bytes)->tv_sec = timeout_sec;
    ((__kernel_timespec *)buf_16bytes)->tv_nsec =
        (timeout_sec - ((__kernel_timespec *)buf_16bytes)->tv_sec) * 1e9;
    io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_timeout(sqe, (__kernel_timespec *)buf_16bytes, 1, 0);
    sqe->user_data = ++cnt;
    io_uring_submit(&ring);
    return cnt;
  }
  inline long long do_cancel(long long user_data, int flags) {
    io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_cancel(sqe, (void *)user_data, flags);
    sqe->user_data = ++cnt;
    io_uring_submit(&ring);
    return cnt;
  }
};
