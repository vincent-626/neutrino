import React from 'react';
import { AppPlugin, DataQuery, RawTimeRange } from '@grafana/data';
import { NeutrinoDrawer } from './components/NeutrinoDrawer';

interface ExploreToolbarActionContext {
  timeRange: RawTimeRange;
  targets?: DataQuery[];
}

export const plugin = new AppPlugin().configureExtensionLink<ExploreToolbarActionContext>({
  extensionPointId: 'grafana/explore/toolbar/action',
  title: 'Neutrino 🔍',
  description: 'Semantic log search',
  onClick: (_, helpers) => {
    const context = helpers.context;
    const datasourceUid = (context?.targets?.[0]?.datasource as { uid?: string } | undefined)?.uid;

    helpers.openModal({
      title: 'Neutrino — Semantic Log Search',
      body: ({ onDismiss }) => (
        <NeutrinoDrawer
          timeRange={context?.timeRange}
          datasourceUid={datasourceUid}
          onDismiss={onDismiss}
        />
      ),
      width: 750,
    });
  },
});
