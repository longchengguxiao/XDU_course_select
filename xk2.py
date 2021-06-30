from pyppeteer import launch
import asyncio
import time
import re
import json

#登录（需要手动输入验证码）
async def login_in(page):
    await page.goto(ori_url)
    await page.waitForSelector('#loginName')
    await page.type('#loginName', XDU_username)
    await page.type('#loginPwd', XDU_password)
    scr = await page.querySelectorEval('#vcodeImg', 'node => node.src')
    print(scr)
    vertify = input('---------------请输入验证码------------')
    await page.type('#verifyCode', vertify)
    await page.click('#studentLoginBtn', options={
        'button': 'left',
        'clickCount': 1,  # 1 or 2
        'delay': 300,  # 毫秒
    })
    s_time = time.time()
    while True:
        try:
            await page.waitForSelector('#courseBtn')
            break
        except:
            await asyncio.sleep(1)
        e_time = time.time()
        if int(e_time-s_time)>10:
            raise RuntimeError('登录超时请重新登陆(可能是验证码出错)')
    await page.click('#courseBtn', options={
        'button': 'left',
        'clickCount': 1,  # 1 or 2
        'delay': 300,  # 毫秒
    })
    #cookies = await page.cookies()
    #await save_cookie(cookies)
    print('------------验证成功------------')
    return page


#检查课程是否可选
async def check_xk(page,num,searchloc):
    flag = 0
    await page.waitForSelector('#publicSearch')
    await asyncio.sleep(0.4)
    while True:
        await page.evaluate('document.querySelector("#publicSearch").value=""')
        await page.type(searchloc, num)
        await asyncio.sleep(0.2)
        await page.keyboard.press('Enter')
        await asyncio.sleep(0.2)
        await page.waitForSelector('.cv-row > div:nth-child(1) > span:nth-child(2)')
        now_name = await page.querySelectorEval('.cv-row > div:nth-child(1) > span:nth-child(2)', 'node => node.innerText')
        if re.match(num, now_name):
            break
        await page.evaluate('document.querySelector("#publicSearch").value=""')
    await page.waitForSelector('.cv-row > div:nth-child(6)')
    normal = 100
    try:
        now_num = int(await page.querySelectorEval('.cv-row > div:nth-child(6)', 'node => node.innerText'))
    except:
        flag = 1
    name = await page.querySelectorEval('.cv-row > div:nth-child(2)', 'node => node.innerText')
    return page, name, flag


#选课冲冲冲
async def rush_xk(page):
    flag = 0
    print('---------------正在等待抢课---------------')
    while not time.mktime(rush_time) - time.time() <= 0.5:
        await asyncio.sleep(0.4)
    print('---------------开始抢课------------------')
    await page.waitForSelector('#publicBody>div>div.cv-setting-col>a')
    # publicBody > div > div.cv-setting-col > a

    await page.click('#publicBody>div>div.cv-setting-col>a', options={
        'button': 'left',
        'clickCount': 1,  # 1 or 2
        'delay': 300,  # 毫秒
    })
    await page.waitForSelector('div.cvBtnFlag:nth-child(1)')
    await page.click('div.cvBtnFlag:nth-child(1)', options={
        'button': 'left',
        'clickCount': 1,  # 1 or 2
        'delay': 300,  # 毫秒
    })
    try:
        await page.waitForSelector('#cvDialog > div:nth-child(2) > div.cv-body > div')
        reason = await page.querySelectorEval('#cvDialog > div:nth-child(2) > div.cv-body > div', 'node => node.innerText')
        print(f'------抢课失败，原因:{reason}--------------')
        flag = 1
    except:
        pass
    await page.reload()
    return page, flag

#主函数
async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()
    page = await login_in(page)
    trans_dict = {"推荐班级选课":"#aRecommendCourse","方案内选课":"#aProgramCourse","方案外选课":"#aUnProgramCourse","通识教育选修即校公选课程":"#aPublicCourse","重修课程":"#aRetakeCourse","体育俱乐部":"#aSportCourse","辅修":"#aMinorCourse"}
    trans_dict2 = {"推荐班级选课":"#recommendSearch","方案内选课":"#programSearch","方案外选课":"##unProgramSearch","通识教育选修即校公选课程":"#publicSearch","重修课程":"#retakeSearch","体育俱乐部":"#sportSearch","辅修":"#minorSearch"}
    for item in xk_items:
        selector = trans_dict[item[0]]
        searchloc = trans_dict2[item[0]]
        await page.waitForSelector(selector)
        await page.click(selector, options={
            'button': 'left',
            'clickCount': 1,  # 1 or 2
            'delay': 300,  # 毫秒
            })
        for num in item[1]:
            cnt = 1
            cnt2 = 1
            s_time = time.time()
            while True:
                page, xk_name, flag_1 = await check_xk(page, num, searchloc)
                if flag_1 == 1:

                    if hard_rush:
                        print(f'--------------人数已满,扔在继续尝试{xk_name}，次数{cnt2}---------------')
                        await page.reload()
                        cnt2 += 1
                        continue
                    else:
                        print(f'---------------已跳过对{xk_name}的抢课----------')
                        break
                page, flag = await rush_xk(page)
                if flag == 0:
                    e_time = time.time()
                    print(f'------------第{cnt}轮抢课成功,{xk_name}已被成功锁定,抢课时长{e_time-s_time}----------')
                    break
                if cnt>=5:
                    print(f'----------抢课失败----------')
                    break
                print(f'------------第{cnt}轮抢课失败----------')
                cnt += 1


if __name__ == '__main__':
    with open('config.json','r',encoding='utf-8') as f:
        config = json.loads(f.read())
    #初始化数据
    ori_url = 'http://xk.xidian.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do'
    xk_items = config["选课内容"].items()
    xk_time = config["选课开始时间"]
    rush_time = time.strptime(xk_time, '%Y-%m-%d %H:%M:%S')
    XDU_username = config["个人信息"]["用户名"]
    XDU_password = config["个人信息"]["密码"]
    hard_rush = config["是否开启硬挤模式"]
    asyncio.get_event_loop().run_until_complete(main())
