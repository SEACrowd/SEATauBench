# Panimula
Ang dokumentong ito ay nagsisilbing komprehensibong gabay para sa mga agent ng teknikal na suporta. Nagbibigay ito ng mga detalyadong pamamaraan at mga hakbang sa pag-troubleshoot para tulungan ang mga user na nakakaranas ng mga karaniwang isyu sa serbisyong cellular ng kanilang telepono, koneksyon sa mobile data, at Multimedia Messaging Service (MMS). Ang manwal ay nakabalangkas upang tulungan ang mga agent na mahusay na ma-diagnose at maresolba ang mga problema sa pamamagitan ng pagbabalangkas kung paano gumagana ang mga serbisyong ito, mga karaniwang isyu, at ang mga tool na available para sa resolusyon.

Ang mga pangunahing seksyong sakop ay:
*   **Pag-unawa at Pag-troubleshoot sa Serbisyong Cellular ng Iyong Telepono**: Tinutugunan ang mga isyu na may kaugnayan sa koneksyon sa network, lakas ng signal, at mga problema sa SIM card.
*   **Pag-unawa at Pag-troubleshoot sa Mobile Data ng Iyong Telepono**: Nakatuon sa mga problema sa internet access sa pamamagitan ng cellular network, kabilang ang bilis at koneksyon.
*   **Pag-unawa at Pag-troubleshoot sa MMS (Pagmemensahe ng Larawan/Video)**: Sinasaklaw ang mga isyu na may kaugnayan sa pagpapadala at pagtanggap ng mga multimedia message.

Siguraduhin na subukan mo ang lahat ng posibleng paraan upang maresolba ang isyu ng user bago ilipat sa isang human agent.

# Ano ang magagawa ng user sa kanilang device
Narito ang mga aksyon na kayang gawin ng isang user sa kanilang device.
Dapat mong maunawaan ang mga ito nang mabuti dahil bilang bahagi ng teknikal na suporta, kakailanganin mong tulungan ang customer na magsagawa ng serye ng mga aksyon

## Mga Aksyong Diagnostic (Read-only)
1. **check_status_bar** - Ipinapakita kung anong mga icon ang kasalukuyang nakikita sa status bar ng iyong telepono (ang lugar sa itaas ng screen).
   - Status ng airplane mode ("✈️ Airplane Mode" kapag naka-enable)
   - Lakas ng signal ng network ("📵 walang serbisyo", "📶¹ mahina", "📶² katamtaman", "📶³ maayos", "📶⁴ napakagaling")
   - Teknolohiya ng network (hal., "5G", "4G", atbp.)
   - Status ng mobile data ("📱 Data Enabled" o "📵 Data Disabled")
   - Status ng data saver ("🔽 Data Saver" kapag naka-enable)
   - Status ng Wi-Fi ("📡 nakakonekta sa [SSID]" o "📡 Enabled")
   - Status ng VPN ("🔒 VPN Connected" kapag nakakonekta)
   - Antas ng baterya ("🔋 [percentage]%")
2. **check_network_status** - Sinusuri ang status ng koneksyon ng iyong telepono sa mga cellular network at Wi-Fi. Ipinapakita ang status ng airplane mode, lakas ng signal, uri ng network, kung naka-enable ang mobile data, at kung naka-enable ang data roaming. Ang lakas ng signal ay maaaring "wala", "mahina" (1 bar), "katamtaman" (2 bar), "maayos" (3 bar), "napakagaling" (4+ bar).
3. **check_network_mode_preference** - Sinusuri ang preference sa network mode ng iyong telepono. Ipinapakita ang uri ng cellular network na gustong ikonekta ng iyong telepono (hal., 5G, 4G, 3G, 2G).
4. **check_sim_status** - Sinusuri kung gumagana nang tama ang iyong SIM card at ipinapakita ang kasalukuyang status nito. Ipinapakita kung ang SIM ay aktibo, nawawala, o naka-lock gamit ang PIN o PUK code.
5. **check_data_restriction_status** - Sinusuri kung ang iyong telepono ay may anumang feature na naglilimita sa data na aktibo. Ipinapakita kung naka-on ang mode na Data Saver at kung ang paggamit ng background data ay restricted sa buong device.
6. **check_apn_settings** - Sinusuri ang mga teknikal na setting ng APN na ginagamit ng iyong telepono upang kumonekta sa mobile data network ng iyong carrier. Ipinapakita ang kasalukuyang pangalan ng APN at MMSC URL para sa pagmemensahe ng larawan.
7. **check_wifi_status** - Sinusuri ang status ng iyong koneksyon sa Wi-Fi. Ipinapakita kung naka-on ang Wi-Fi, kung saang network ka nakakonekta (kung mayroon), at ang lakas ng signal.
8. **check_wifi_calling_status** - Sinusuri kung naka-enable ang Wi-Fi Calling sa iyong device. Pinapayagan ka ng feature na ito na gumawa at tumanggap ng mga tawag sa isang Wi-Fi network sa halip na gamitin ang cellular network.
9. **check_vpn_status** - Sinusuri kung gumagamit ka ng koneksyon sa VPN (Virtual Private Network). Ipinapakita kung ang isang VPN ay aktibo, nakakonekta, at ipinapakita ang anumang detalye ng koneksyon na available.
10. **check_installed_apps** - Ibinabalik ang pangalan ng lahat ng naka-install na app sa telepono.
11. **check_app_status** - Sinusuri ang detalyadong impormasyon tungkol sa isang partikular na app. Ipinapakita ang mga pahintulot nito at mga setting ng paggamit ng background data.
12. **check_app_permissions** - Sinusuri kung anong mga pahintulot ang kasalukuyang mayroon ang isang partikular na app. Ipinapakita kung ang app ay may access sa mga feature tulad ng storage, camera, lokasyon, atbp.
13. **run_speed_test** - Sinusukat ang iyong kasalukuyang bilis ng koneksyon sa internet (bilis ng download). Nagbibigay ng impormasyon tungkol sa kalidad ng koneksyon at kung anong mga aktibidad ang kaya nitong suportahan. Ang bilis ng download ay maaaring "hindi alam", "very mahina", "mahina", "katamtaman", "maayos", o "napakagaling".
14. **can_send_mms** - Sinusuri kung ang messaging app ay nakakapagpadala ng mga mensaheng MMS.

## Mga Aksyong Fix (Write/Modify)
1. **set_network_mode_preference** - Binabago ang uri ng cellular network na gustong ikonekta ng iyong telepono. Ang mga network na may mas mataas na bilis (5G, 4G) ay nagbibigay ng mas mabilis na data ngunit maaaring gumamit ng mas maraming baterya.
2. **toggle_airplane_mode** - Ino-on o ino-off ang Airplane Mode. Kapag naka-ON, dinidiskonekta nito ang lahat ng wireless na komunikasyon kabilang ang cellular, Wi-Fi, at Bluetooth.
3. **reseat_sim_card** - Ginagaya ang pagtanggal at muling pagpasok sa iyong SIM card. Makakatulong ito na maresolba ang mga isyu sa pagkilala.
4. **toggle_data** - Ino-on o ino-off ang koneksyon ng mobile data ng iyong telepono. Kinokontrol kung ang iyong telepono ay makakagamit ng cellular data para sa internet access kapag hindi available ang Wi-Fi.
5. **toggle_roaming** - Ino-on o ino-off ang Data Roaming. Kapag naka-ON, naka-enable ang roaming at ang iyong telepono ay makakagamit ng mga data network sa mga lugar sa labas ng coverage ng iyong carrier.
6. **toggle_data_saver_mode** - Ino-on o ino-off ang mode na Data Saver. Kapag naka-ON, binabawasan nito ang paggamit ng data, na maaaring makaapekto sa bilis ng data.
7. **set_apn_settings** - Itinatakda ang mga setting ng APN para sa telepono.
8. **reset_apn_settings** - Ino-reset ang iyong mga setting ng APN sa mga default na setting.
9. **toggle_wifi** - Ino-on o ino-off ang Wi-Fi radio ng iyong telepono. Kinokontrol kung ang iyong telepono ay makakatuklas at makakakonekta sa mga wireless network para sa internet access.
10. **toggle_wifi_calling** - Ino-on o ino-off ang Wi-Fi Calling. Pinapayagan ka ng feature na ito na gumawa at tumanggap ng mga tawag sa Wi-Fi sa halip na sa cellular network, na makakatulong sa mga lugar na may mahinang cellular signal.
11. **connect_vpn** - Kumokonekta sa iyong VPN (Virtual Private Network).
12. **disconnect_vpn** - Dinidiskonekta ang anumang aktibo koneksyon sa VPN (Virtual Private Network). Itinitigil ang pagruruta ng iyong trapiko sa internet sa pamamagitan ng isang VPN server, na maaaring makaapekto sa bilis ng koneksyon o access sa nilalaman.
13. **grant_app_permission** - Nagbibigay ng partikular na pahintulot sa isang app (tulad ng access sa storage, camera, o lokasyon). Kinakailangan para sa ilang function ng app na gumana nang maayos.
14. **reboot_device** - Ganap na nire-restart ang iyong telepono. Makakatulong ito na maresolba ang maraming pansamantalang glitch sa software sa pamamagitan ng pag-refresh sa lahat ng tumatakbong serbisyo at koneksyon.

# Pag-unawa at Pag-troubleshoot sa Serbisyong Cellular ng Iyong Telepono
Ang seksyong ito ay nagdedetalye para sa mga agent kung paano ikinokonekta ng telepono ng isang user sa cellular network (madalas na tinutukoy bilang "serbisyo") at nagbibigay ng mga pamamaraan upang ma-troubleshoot ang mga karaniwang isyu. Ang maayos na serbisyong cellular ay kinakailangan para sa mga tawag, text, at mobile data.

## Mga Karaniwang Isyu sa Serbisyo at ang Kanilang mga Sanhi
Kung ang user ay nakakaranas ng mga problema sa serbisyo, narito ang ilang karaniwang sanhi:

*   **Naka-ON ang Airplane Mode**: Dinidiskonekta nito ang lahat ng wireless radio, kabilang ang cellular.
*   **Mga Problema sa SIM Card**:
    *   Hindi nakapasok o hindi maayos ang pagkakalagay.
    *   Naka-lock dahil sa maling pag-input ng PIN/PUK.
*   **Maling Mga Setting ng Network**: Maaaring mali ang mga setting ng APN na nagreresulta sa pagkawala ng serbisyo.
*   **Mga Isyu sa Carrier**: Maaaring hindi aktibo ang iyong linya dahil sa mga problema sa pagsingil.


## Pag-diagnose ng mga Isyu sa Serbisyo
Ang `check_status_bar()` ay maaaring gamitin upang suriin kung ang user ay nahaharap sa isyu sa serbisyo.
Kung may serbisyong cellular, magbabalik ang status bar ng indicator ng lakas ng signal.

## Pag-troubleshoot sa mga Problema sa Serbisyo
### Airplane Mode
Ang Airplane Mode ay isang feature na nagdidiskonekta sa lahat ng wireless radio, kabilang ang cellular. Kung ito ay naka-enable, pipigilan nito ang anumang koneksyon sa cellular.
Maaari mong suriin kung naka-ON ang Airplane Mode sa pamamagitan ng paggamit ng `check_status_bar()` o `check_network_status()`.
Kung ito ay naka-ON, gabayan ang user na gamitin ang `toggle_airplane_mode()` upang i-OFF ito.

### Mga Isyu sa SIM Card
Ang SIM card ay ang pisikal na card na naglalaman ng impormasyon ng user at nagpapahintulot sa telepono na kumonekta sa cellular network.
Ang mga problema sa SIM card ay maaaring humantong sa kumpletong pagkawala ng serbisyo.
Ang pinakakaraniwang isyu ay hindi maayos ang pagkakalagay ng SIM card o nag-input ang user ng maling PIN o PUK code.
Gamitin ang `check_sim_status()` upang suriin ang status ng SIM card.
Kung ito ay nagpapakita ng "nawawala", gabayan ang user na gamitin ang `reseat_sim_card()` upang matiyak na tama ang pagkakalagay ng SIM card.
Kung ito ay nagpapakita ng "naka-lock" (dahil sa maling pag-input ng PIN o PUK), **mag-escalate sa teknikal na suporta para sa tulong sa seguridad ng SIM**.
Kung ito ay nagpapakita ng "Aktibo", malamang na maayos ang mismong SIM.

### Maling Mga Setting ng APN
Ang mga setting ng Access Point Name (APN) ay mahalaga para sa koneksyon sa network.
Kung ang `check_apn_settings()` ay nagpapakita ng "Mali", gabayan ang user na gamitin ang `reset_apn_settings()` upang i-reset ang mga setting ng APN.
Pagkatapos i-reset ang mga setting ng APN, dapat turuan ang user na gamitin ang `reboot_device()` para mailapat ang mga pagbabago.

### Suspensyon ng Linya
Kung ang linya ay suspendido, ang user ay walang serbisyong cellular.
Imbestigahan kung ang linya ay suspendido. Sumangguni sa pangkalahatang patakaran ng agent para sa mga alituntunin sa paghawak ng mga suspensyon ng linya.
*   Kung ang linya ay suspendido at kayang alisin ng agent ang suspensyon (ayon sa pangkalahatang patakaran), suriin kung naibalik na ang serbisyo.
*   Kung ang suspensyon ay hindi kayang alisin ng agent (hal., dahil sa petsa ng pagtatapos ng kontrata gaya ng nabanggit sa pangkalahatang patakaran, o mga dahilan na iba pa na hindi kayang resolbahin ng agent), **mag-escalate sa teknikal na suporta**.


# Pag-unawa at Pag-troubleshoot sa Mobile Data ng Iyong Telepono
Ang seksyong ito ay nagpapaliwanag para sa mga agent kung paano ginagamit ng telepono ng isang user ang mobile data para sa internet access kapag hindi available ang Wi-Fi, at nagdedetalye ng pag-troubleshoot para sa mga karaniwang isyu sa koneksyon at bilis.

## Ano ang Mobile Data?
Pinapayagan ng mobile data ang telepono na kumonekta sa internet gamit ang cellular network ng carrier. Binibigyang-daan nito ang pag-browse sa mga website, paggamit ng mga app, streaming ng video, at pagpapadala/pagtanggap ng mga email kapag hindi nakakonekta sa Wi-Fi. Ang status bar ay karaniwang nagpapakita ng mga icon tulad ng "5G", "LTE", "4G", "3G", "H+", o "E" upang ipahiwatig ang isang aktibo koneksyon sa mobile data at ang uri nito.

## Mga Kinakailangan para sa Mobile Data
Para gumana ang mobile data, dapat ay mayroon munang **serbisyong cellular** ang user. Sumangguni sa gabay na "Pag-unawa at Pag-troubleshoot sa Serbisyong Cellular ng Iyong Telepono" kung ang user ay walang serbisyo.

## Mga Karaniwang Isyu sa Mobile Data at mga Sanhi
Kahit may serbisyong cellular, maaaring magkaroon ng mga problema sa mobile data. Kasama sa mga karaniwang dahilan ang:

*   **Naka-ON ang Airplane Mode**: Dinidiskonekta ang lahat ng wireless na koneksyon, kabilang ang mobile data.
*   **Naka-OFF ang Mobile Data**: Maaaring naka-disable ang pangunahing switch para sa mobile data sa mga setting ng telepono.
*   **Mga Isyu sa Roaming (Kapag ang User ay nasa Ibang Bansa)**:
    *   Naka-OFF ang Data Roaming sa telepono.
    *   Ang linya ay walang roaming.
*   **Naabot ang mga Limitasyon ng Data Plan**: Maaaring nagamit na ng user ang kanilang buwanang allowance sa data, at pinabagal o pinutol ng carrier ang data.
*   **Naka-ON ang Data Saver Mode**: Nililimitahan ng feature na ito ang paggamit ng background data at maaaring maging mabagal o hindi tumutugon ang ilang app o serbisyo para makatipid sa data.
*   **Mga Isyu sa VPN**: Ang isang aktibo koneksyon sa VPN ay maaaring mabagal o maling na-configure, na nakakaapekto sa bilis ng data o koneksyon.
*   **Maling Mga Preference sa Network**: Ang telepono ay nakatakda sa mas lumang teknolohiya ng network tulad ng 2G/3G.

## Pag-diagnose ng mga Isyu sa Mobile Data
Ang `run_speed_test()` ay maaaring gamitin upang suriin ang mga posibleng isyu sa mobile data.
Kapag hindi available ang mobile data, dapat magbalik ang speed test ng 'no connection'.
Kung ang data ay available, magbabalik din ang speed test ng bilis ng data.
Anumang bilis na mas mababa sa 'Napakagaling' ay itinuturing na mabagal.

## Pag-troubleshoot sa mga Problema sa Mobile Data
### Airplane Mode
Sumangguni sa seksyong "Pag-unawa at Pag-troubleshoot sa Serbisyong Cellular ng Iyong Telepono" para sa mga tagubilin kung paano suriin at i-off ang Airplane Mode.

### Naka-disable ang Mobile Data
Ang switch ng mobile data ay nagpapahintulot sa telepono na kumonekta sa internet gamit ang cellular network ng carrier.
Kung ang `check_network_status()` ay nagpapakita na ang mobile data ay naka-disable, gabayan ang user na gamitin ang `toggle_data()` upang i-ON ang mobile data.

### Pagtugon sa mga Problema sa Data Roaming
Pinapayagan ng data roaming ang user na gamitin ang koneksyon ng data ng kanilang telepono sa mga lugar sa labas ng kanilang home network (hal. kapag naglalakbay sa ibang bansa).
Kung ang user ay nasa labas ng pangunahing coverage area ng kanilang carrier (roaming) at hindi gumagana ang mobile data, gabayan sila na gamitin ang `toggle_roaming()` upang matiyak na naka-ON ang Data Roaming.
Dapat mong suriin kung ang linya na nauugnay sa telepono na numero na ibinigay ng user ay may roaming. Kung wala, hindi magagamit ng user ang koneksyon ng data ng kanilang telepono sa mga lugar sa labas ng kanilang home network.
Sumangguni sa pangkalahatang patakaran para sa mga alituntunin sa pag-enable ng roaming.

### Data Saver Mode
Ang Data Saver mode ay isang feature na naglilimita sa paggamit ng background data at maaaring makaapekto sa bilis ng data.
Kung ang `check_data_restriction_status()` ay nagpapakita na "Ang mode na Data Saver ay naka-ON", gabayan ang user na gamitin ang `toggle_data_saver_mode()` upang i-OFF ito.

### Mga Isyu sa Koneksyon sa VPN
Ang VPN (Virtual Private Network) ay isang feature na nag-e-encrypt sa trapiko sa internet at makakatulong upang mapabuti ang bilis ng data at seguridad.
Gayunpaman, sa ilang mga kaso, ang VPN ay maaaring maging sanhi ng malaking pagbaba ng bilis.
Kung ang `check_vpn_status()` ay nagpapakita na "Ang VPN ay naka-ON at nakakonekta" at ang antas ng pagganap ay "Mahina", gabayan ang user na gamitin ang `disconnect_vpn()` upang i-disconnect ang VPN.

### Naabot ang mga Limitasyon ng Data Plan
Ang bawat plan ay tumutukoy sa maximum na paggamit ng data bawat buwan.
Kung ang paggamit ng data ng user para sa isang linya na nauugnay sa telepono na numero na ibinigay ng user ay lumampas sa limitasyon ng data ng plan, mawawala ang koneksyon ng data.
Ang user ay may 2 opsyon:
- Lumipat sa isang plan na may mas maraming data.
- Magdagdag ng higit pang data sa linya sa pamamagitan ng "pag-refuel" ng data sa presyong bawat GB na tinutukoy ng plan.
Sumangguni sa pangkalahatang patakaran para sa mga alituntunin sa mga opsyon na iyon.

### Pag-optimize sa mga Preference sa Network Mode
Ang mga preference sa network mode ay ang mga setting na tumutukoy sa uri ng cellular network na ikokonekta ng telepono.
Ang paggamit ng mga mas lumang mode tulad ng 2G/3G ay maaaring makabuluhang maglimita sa bilis.
Kung ang `check_network_mode_preference()` ay nagpapakita ng "2G" o "3G", gabayan ang user na gamitin ang `set_network_mode_preference(mode: str)` na may mode na `"mas gusto ang 4G/5G"` upang payagan ang telepono na kumonekta sa 5G.

# Pag-unawa at Pag-troubleshoot sa MMS (Pagmemensahe ng Larawan/Video)
Ang seksyong ito ay nagpapaliwanag para sa mga agent kung paano i-troubleshoot ang Multimedia Messaging Service (MMS), na nagpapahintulot sa mga user na magpadala at tumanggap ng mga mensahe na naglalaman ng mga larawan, video, o audio.

## Ano ang MMS?
Ang MMS ay isang extension ng SMS (text messaging) na nagpapahintulot para sa multimedia content. Kapag ang isang user ay nagpadala ng larawan sa isang kaibigan sa pamamagitan ng kanilang messaging app, karaniwan nilang ginagamit ang MMS.

## Mga Kinakailangan para sa MMS
Para gumana ang MMS, ang user ay dapat may serbisyong cellular at mobile data (anumang bilis).
Sumangguni sa mga seksyong "Pag-unawa at Pag-troubleshoot sa Serbisyong Cellular ng Iyong Telepono" at "Pag-unawa at Pag-troubleshoot sa Mobile Data ng Iyong Telepono" para sa karagdagang impormasyon.

## Mga Karaniwang Isyu sa MMS at mga Sanhi
*   **Walang Serbisyong Cellular o Naka-OFF/Hindi Gumagana ang Mobile Data**: Ang mga pinakakaraniwang dahilan. Umaasa ang MMS sa mga ito.
*   **Maling Mga Setting ng APN**: Partikular, isang nawawala o maling MMSC URL.
*   **Nakakonekta sa 2G Network**: Ang mga network na 2G ay karaniwang hindi angkop para sa MMS.
*   **Configuration ng Wi-Fi Calling**: Sa ilang mga kaso, kung paano naka-configure ang Wi-Fi Calling ay maaaring makaapekto sa MMS, lalo na kung hindi sinusuportahan ng iyong carrier ang MMS sa Wi-Fi.
*   **Mga Pahintulot sa App**: Ang messaging app ay nangangailangan ng pahintulot na ma-access ang storage (para sa mga media file) at karaniwan ay ang mga functionality ng SMS.

## Pag-diagnose ng mga Isyu sa MMS
Ang tool na `can_send_mms()` sa telepono ng user ay maaaring gamitin upang suriin kung ang user ay nahaharap sa isyu sa MMS.

## Pag-troubleshoot sa mga Problema sa MMS
### Pagtitiyak ng Batayang Koneksyon para sa MMS
Ang matagumpay na pagmemensahe ng MMS ay umaasa sa pundamental na serbisyo at koneksyon sa data. Ang seksyong ito ay sumasaklaw sa pag-verify sa mga kinakailangang ito.
Una, tiyakin na ang user ay nakakagawa ng mga tawag at ang kanilang mobile data ay gumagana para sa mga iba pa app (hal., pag-browse sa web). Sumangguni sa mga seksyong "Pag-unawa at Pag-troubleshoot sa Serbisyong Cellular ng Iyong Telepono" at "Pag-unawa at Pag-troubleshoot sa Mobile Data ng Iyong Telepono" kung kinakailangan.

### Hindi Angkop na Teknolohiya ng Network para sa MMS
Ang MMS ay may mga partikular na kinakailangan sa network; ang mga mas lumang teknolohiya tulad ng 2G ay hindi sapat. Ang seksyong ito ay nagpapaliwanag kung paano suriin ang uri ng network at baguhin ito kung kinakailangan.
Ang MMS ay nangangailangan ng kahit man lang 3G na koneksyon sa network; ang mga network na 2G ay karaniwang hindi angkop.
Kung ang `check_network_status()` ay nagpapakita ng "2G", gabayan ang user na gamitin ang `set_network_mode_preference(mode: str)` upang lumipat sa isang network mode na may kasamang 3G, 4G, o 5G (hal., `"mas gusto ang 4G/5G"` o `"4G lang"`).

### Pag-verify sa APN (MMSC URL) para sa MMS
Ang MMSC ay ang Multimedia Messaging Service Center. Ito ang server na humahawak sa mga mensaheng MMS. Kung walang tamang MMSC URL, ang user ay hindi makakapagpadala o makakatanggap ng mga mensaheng MMS.
Ang mga iyon ay tinutukoy bilang bahagi ng mga setting ng APN. Ang maling MMSC URL ay isang napakakaraniwang dahilan ng mga isyu sa MMS.
Kung ang `check_apn_settings()` ay nagpapakita na ang MMSC URL ay hindi nakatakda, gabayan ang user na gamitin ang `reset_apn_settings()` upang i-reset ang mga setting ng APN.
Pagkatapos i-reset ang mga setting ng APN, dapat turuan ang user na gamitin ang `reboot_device()` para mailapat ang mga pagbabago.

### Pag-iimbestiga sa Interference ng Wi-Fi Calling sa MMS
Ang mga setting ng Wi-Fi Calling ay maaaring kung minsan ay sumalungat sa functionality ng MMS.
Kung ang `check_wifi_calling_status()` ay nagpapakita na "Ang Wi-Fi Calling ay naka-ON", gabayan ang user na gamitin ang `toggle_wifi_calling()` upang i-OFF ito.

### Kulang sa Kinakailangang mga Pahintulot ang Messaging App
Ang messaging app ay nangangailangan ng mga partikular na pahintulot upang mahawakan ang media at makapagpadala ng mga mensahe.
Kung ang `check_app_permissions(app_name="messaging")` ay nagpapakita na ang mga pahintulot sa "storage" at "sms" ay hindi nakalista bilang ipinagkaloob, gabayan ang user na gamitin ang `grant_app_permission(app_name="messaging", permission="storage")` at `grant_app_permission(app_name="messaging", permission="sms")` upang ibigay ang mga kinakailangang pahintulot.