@echo off

set "TOKEN=YOUR-ACCESS-TOKEN"
set "REPO=35984297"

rem This script downloads these files:

rem AvatarExcelConfigData.json
rem AvatarSkillDepotExcelConfigData.json
rem AvatarSkillExcelConfigData.json
rem ManualTextMapConfigData.json
rem WeaponExcelConfigData.json
rem TextMapRU.json

echo Downloading AvatarExcelConfigData.json
curl -sSfL -H "PRIVATE-TOKEN: %TOKEN%" "https://gitlab.com/api/v4/projects/%REPO%/repository/files/Resources%%2FExcelBinOutput%%2FAvatarExcelConfigData.json/raw" -o AvatarExcelConfigData.json
echo Downloading AvatarSkillDepotExcelConfigData.json
curl -sSfL -H "PRIVATE-TOKEN: %TOKEN%" "https://gitlab.com/api/v4/projects/%REPO%/repository/files/Resources%%2FExcelBinOutput%%2FAvatarSkillDepotExcelConfigData.json/raw" -o AvatarSkillDepotExcelConfigData.json
echo Downloading AvatarSkillExcelConfigData.json
curl -sSfL -H "PRIVATE-TOKEN: %TOKEN%" "https://gitlab.com/api/v4/projects/%REPO%/repository/files/Resources%%2FExcelBinOutput%%2FAvatarSkillExcelConfigData.json/raw" -o AvatarSkillExcelConfigData.json
echo Downloading ManualTextMapConfigData.json
curl -sSfL -H "PRIVATE-TOKEN: %TOKEN%" "https://gitlab.com/api/v4/projects/%REPO%/repository/files/Resources%%2FExcelBinOutput%%2FManualTextMapConfigData.json/raw" -o ManualTextMapConfigData.json
echo Downloading WeaponExcelConfigData.json
curl -sSfL -H "PRIVATE-TOKEN: %TOKEN%" "https://gitlab.com/api/v4/projects/%REPO%/repository/files/Resources%%2FExcelBinOutput%%2FWeaponExcelConfigData.json/raw" -o WeaponExcelConfigData.json

echo Downloading TextMapRU.json
curl -sSfL -H "PRIVATE-TOKEN: %TOKEN%" "https://gitlab.com/api/v4/projects/%REPO%/repository/files/Resources%%2FTextMap%%2FTextMapRU.json/raw" -o TextMapRU.json

echo Done.
