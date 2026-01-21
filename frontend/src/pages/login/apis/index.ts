import type * as Auth from "./type"

/** 获取登录验证码 */
export function getCaptchaApi() {
  // 返回模拟验证码数据
  return Promise.resolve({
    code: 0,
    data: "1234",
    message: "获取验证码成功"
  })
}

/** 登录并返回 Token */
export function loginApi(data: Auth.LoginRequestData) {
  // 简单的本地登录验证
  if (data.username === "admin" && data.password === "123456" && data.code === "1234") {
    return Promise.resolve({
      code: 0,
      data: { token: `mock-token-${Date.now()}` },
      message: "登录成功"
    })
  } else {
    return Promise.resolve({
      code: 401,
      data: null,
      message: "用户名或密码错误"
    })
  }
}
