---
layout: post
title: "Github Pages 服务的域名设置"
subtitle: ""
date: 2014-05-06 22:51:00
author: Le
header_img: "img/post-bg-2015.jpg"
tags:
    - github
    - catcat
    - blog
---




这几天每次 Push 博客到 Github Pages 时总会收到一封邮件：

> 
> The page build completed successfully, but returned the following warning:
> 
> GitHub Pages recently underwent some improvements (https://github.com/blog/1715-faster-more-awesome-github-pages) to make your site faster and more awesome, but we've noticed that iforget.info isn't properly configured to take advantage of these new features. While your site will continue to work just fine, updating your domain's configuration offers some additional speed and performance benefits. Instructions on updating your site's IP address can be found at
> https://help.github.com/articles/setting-up-a-custom-domain-with-github-pages#step-2-configure-dns-records, and of course, you can always get in touch with a human at support@github.com. For the more technical minded folks who want to skip the help docs: your site's DNS records are pointed to a deprecated IP address. 
> 
> For information on troubleshooting Jekyll see:
> 
> https://help.github.com/articles/using-jekyll-with-pages#troubleshooting
> 
> If you have any questions please contact us at https://github.com/contact.
> 

大概意思就是我们 Github Pages 服务最近做了升级，这个升级将会使你的博客访问起来快到碉堡了，赶快来配置(修改域名记录就可以)一下用上吧。

之前 iforget.info 这个域名有两条记录：

- A 记录： iforget.info 到 207.97.227.245
- CNAME(Alias) 记录：www.iforget.info  到  iforget.info 

207.97.227.245 是个美帝的 IP，所以速度比较慢。我还想着给 iforget.info 备个案，从此用上七牛的 CND 来加速了。好消息来了，Github Pages 支持全球 CDN 了，赶紧修改一下 DNS 记录(把之前的记录都删掉吧)：

- CNAME 记录: iforget.info 到 thisiswangle.github.io
- CNAME 记录: www.iforget.info 到 thisiswangle.github.io

好了，静候 DNS 生效。

```
➜  ~  dig iforget.info +nostats +nocomments +nocmd

; <<>> DiG 9.8.3-P1 <<>> iforget.info +nostats +nocomments +nocmd
;; global options: +cmd
;iforget.info.                  IN      A
iforget.info.           30      IN      CNAME   thisiswangle.github.io.
thisiswangle.github.io. 1976    IN      CNAME   github.map.fastly.net.
github.map.fastly.net.  30      IN      A       103.245.222.133
fastly.net.             73096   IN      NS      ns3.p04.dynect.net.
fastly.net.             73096   IN      NS      ns4.p04.dynect.net.
fastly.net.             73096   IN      NS      ns2.p04.dynect.net.
fastly.net.             73096   IN      NS      ns1.p04.dynect.net.
ns1.p04.dynect.net.     74973   IN      A       208.78.70.4
ns2.p04.dynect.net.     74756   IN      A       204.13.250.4
ns3.p04.dynect.net.     74789   IN      A       208.78.71.4
ns4.p04.dynect.net.     153     IN      A       204.13.251.4
```

IP 变成了 103.245.222.133, 澳大利亚 IP ，进入亚洲组了。

当同时设置了 iforget.info 和 www.iforget.info, 再添加一个 CNAME 文件到自己的博客根目录下。

如果 CNAME 的内容是

>
> iforget.info 
>

浏览器中输入 www.iforget.info 时，Github Pages 将会永久跳转(301)到 iforget.info, 反之亦然。

如果你能看到本页，说明本站已经拿到了 GFW 认证。

