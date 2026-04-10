import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "10s", target: 5 },
    { duration: "20s", target: 10 },
    { duration: "10s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"],
    http_req_failed: ["rate<0.1"],
  },
};

const BASE_URL = "http://localhost:8000";

export default function () {
  const res = http.get(`${BASE_URL}/test`);
  check(res, {
    "status 200": (r) => r.status === 200,
    "responde ok": (r) => r.json("ok") === true,
  });
  sleep(1);
}
