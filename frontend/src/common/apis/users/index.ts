import type * as Users from "./type"

/** 获取当前登录用户详情 */
export function getCurrentUserApi() {
  // 返回模拟用户数据
  return Promise.resolve({
    code: 0,
    data: {
      id: 1,
      username: "admin",
      nickname: "管理员",
      avatar: "https://avatars.githubusercontent.com/u/44761321",
      roles: ["admin"]
    },
    message: "获取用户信息成功"
  })
}
