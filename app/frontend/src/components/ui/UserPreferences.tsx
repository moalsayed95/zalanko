import { useTranslation } from "react-i18next";
import * as Icons from "lucide-react";
import { Preferences } from "@/types";

interface UserPreferencesProps {
    preferences?: Preferences;
}

export default function UserPreferences({ preferences }: UserPreferencesProps) {
    const { t } = useTranslation();

    if (!preferences) {
        return (
            <div className="rounded-lg border border-gray-700 bg-gray-800 p-4">
                <h2 className="mb-2 text-lg font-semibold text-white">{t("Your Preferences")}</h2>
                <p className="text-sm text-gray-400">{t("Start a conversation to set your preferences")}</p>
            </div>
        );
    }

    // Dynamic icon component rendering
    const IconComponent = (iconName: string) => {
        const Icon = Icons[iconName as keyof typeof Icons] as React.ElementType;
        return Icon ? <Icon className="h-4 w-4" /> : null;
    };

    return (
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-4">
            <h2 className="mb-4 text-lg font-semibold text-white">{t("Your Preferences")}</h2>

            {preferences.budget && preferences.budget.min !== undefined && preferences.budget.max !== undefined && (
                <div className="mb-3">
                    <h3 className="flex items-center gap-2 text-sm font-medium text-gray-300">
                        <Icons.Wallet className="h-4 w-4 text-purple-400" />
                        {t("Budget")}
                    </h3>
                    <p className="text-sm text-gray-400">
                        €{preferences.budget.min.toLocaleString()} - €{preferences.budget.max.toLocaleString()}
                    </p>
                </div>
            )}

            {preferences.size && preferences.size.min !== undefined && preferences.size.max !== undefined && (
                <div className="mb-3">
                    <h3 className="flex items-center gap-2 text-sm font-medium text-gray-300">
                        <Icons.Square className="h-4 w-4 text-purple-400" />
                        {t("Size")}
                    </h3>
                    <p className="text-sm text-gray-400">
                        {preferences.size.min}m² - {preferences.size.max}m²
                    </p>
                </div>
            )}

            {preferences.rooms && (
                <div className="mb-3">
                    <h3 className="flex items-center gap-2 text-sm font-medium text-gray-300">
                        <Icons.LayoutGrid className="h-4 w-4 text-purple-400" />
                        {t("Rooms")}
                    </h3>
                    <p className="text-sm text-gray-400">{preferences.rooms}</p>
                </div>
            )}

            {preferences.location && (
                <div className="mb-3">
                    <h3 className="flex items-center gap-2 text-sm font-medium text-gray-300">
                        <Icons.MapPin className="h-4 w-4 text-purple-400" />
                        {t("Location")}
                    </h3>
                    <p className="text-sm text-gray-400">{preferences.location}</p>
                </div>
            )}

            {preferences.features && preferences.features.length > 0 && (
                <div className="mb-3">
                    <h3 className="text-sm font-medium text-gray-300">{t("Features")}</h3>
                    <div className="mt-2 flex flex-wrap gap-2">
                        {preferences.features
                            .filter(feature => feature.enabled)
                            .map(feature => (
                                <span key={feature.id} className="flex items-center gap-1 rounded-full bg-purple-900/30 px-2 py-1 text-xs text-purple-300">
                                    {IconComponent(feature.icon)}
                                    {feature.label}
                                </span>
                            ))}
                    </div>
                </div>
            )}
        </div>
    );
}
